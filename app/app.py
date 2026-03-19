import os
import socket
import datetime
import time
import psycopg2
import redis
from flask import Flask, render_template, jsonify, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY", "dev-secret-key")

# --- Métriques Prometheus ---
REQUEST_COUNT = Counter(
    'flask_http_request_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'flask_http_request_duration_seconds',
    'HTTP request latency',
    ['endpoint']
)

@app.before_request
def start_timer():
    from flask import g
    g.start_time = time.time()

@app.after_request
def record_metrics(response):
    from flask import g, request
    latency = time.time() - getattr(g, 'start_time', time.time())
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(endpoint=request.path).observe(latency)
    return response

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

def get_redis():
    return redis.Redis(
        host=os.environ.get("REDIS_HOST", "redis"),
        port=6379,
        password=os.environ.get("REDIS_PASSWORD", ""),
        decode_responses=True
    )

def get_db_primary():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_PRIMARY_HOST", "postgres-primary"),
        database=os.environ.get("POSTGRES_DB", "infralab"),
        user=os.environ.get("POSTGRES_USER", "infralab_user"),
        password=os.environ.get("POSTGRES_PASSWORD", "password")
    )

def get_db_replica():
    try:
        return psycopg2.connect(
            host=os.environ.get("POSTGRES_REPLICA_HOST", "postgres-replica"),
            database=os.environ.get("POSTGRES_DB", "infralab"),
            user=os.environ.get("POSTGRES_USER", "infralab_user"),
            password=os.environ.get("POSTGRES_PASSWORD", "password")
        )
    except Exception:
        return get_db_primary()

@app.route("/")
def index():
    hostname = socket.gethostname()
    r = get_redis()
    visits = r.incr("visit_count")
    return render_template("index.html",
        hostname=hostname,
        visits=visits,
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        environment=os.environ.get("APP_ENV", "development")
    )

@app.route("/health")
def health():
    checks = {"status": "healthy", "checks": {}}
    try:
        conn = get_db_primary()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        checks["checks"]["postgres_primary"] = "ok"
    except Exception as e:
        checks["checks"]["postgres_primary"] = f"error: {str(e)}"
        checks["status"] = "degraded"
    try:
        r = get_redis()
        r.ping()
        checks["checks"]["redis"] = "ok"
    except Exception as e:
        checks["checks"]["redis"] = f"error: {str(e)}"
        checks["status"] = "degraded"
    status_code = 200 if checks["status"] == "healthy" else 503
    return jsonify(checks), status_code

@app.route("/api/info")
def api_info():
    return jsonify({
        "hostname": socket.gethostname(),
        "app_version": "1.0.0",
        "environment": os.environ.get("APP_ENV", "development"),
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route("/api/db-status")
def db_status():
    result = {"primary": {}, "replica": {}}
    try:
        conn = get_db_primary()
        cur = conn.cursor()
        cur.execute("SELECT pg_is_in_recovery(), current_timestamp")
        row = cur.fetchone()
        cur.execute("SELECT pg_current_wal_lsn()")
        wal = cur.fetchone()
        cur.execute("SELECT count(*) FROM pg_stat_replication")
        rep_count = cur.fetchone()
        result["primary"] = {
            "is_replica": row[0],
            "timestamp": str(row[1]),
            "status": "ok",
            "wal_lsn": str(wal[0]) if wal else "N/A",
            "connected_replicas": rep_count[0] if rep_count else 0
        }
        cur.close()
        conn.close()
    except Exception as e:
        result["primary"]["status"] = f"error: {str(e)}"
    try:
        conn = get_db_replica()
        cur = conn.cursor()
        cur.execute("SELECT pg_is_in_recovery(), current_timestamp")
        row = cur.fetchone()
        cur.execute("SELECT pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn()")
        wal = cur.fetchone()
        result["replica"] = {
            "is_replica": row[0],
            "timestamp": str(row[1]),
            "status": "ok",
            "receive_lsn": str(wal[0]) if wal and wal[0] else "N/A",
            "replay_lsn": str(wal[1]) if wal and wal[1] else "N/A"
        }
        cur.close()
        conn.close()
    except Exception as e:
        result["replica"]["status"] = f"error: {str(e)}"
    return jsonify(result)

@app.route("/api/services")
def services_status():
    """Endpoint pour le dashboard - vérifie tous les services"""
    services = {}

    # Redis
    try:
        r = get_redis()
        info = r.info()
        services["redis"] = {
            "status": "online",
            "uptime_seconds": info.get("uptime_in_seconds", 0),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "N/A"),
            "total_keys": r.dbsize()
        }
    except Exception as e:
        services["redis"] = {"status": "offline", "error": str(e)}

    # Postgres Primary
    try:
        conn = get_db_primary()
        cur = conn.cursor()
        cur.execute("SELECT pg_database_size(current_database()), count(*) FROM pg_stat_activity")
        row = cur.fetchone()
        cur.execute("SELECT count(*) FROM pg_stat_replication")
        reps = cur.fetchone()
        services["postgres_primary"] = {
            "status": "online",
            "db_size_mb": round(row[0] / 1048576, 2) if row else 0,
            "active_connections": row[1] if row else 0,
            "replicas_connected": reps[0] if reps else 0
        }
        cur.close()
        conn.close()
    except Exception as e:
        services["postgres_primary"] = {"status": "offline", "error": str(e)}

    # Postgres Replica
    try:
        conn = get_db_replica()
        cur = conn.cursor()
        cur.execute("SELECT pg_is_in_recovery()")
        row = cur.fetchone()
        services["postgres_replica"] = {
            "status": "online" if row and row[0] else "warning",
            "is_recovering": row[0] if row else False
        }
        cur.close()
        conn.close()
    except Exception as e:
        services["postgres_replica"] = {"status": "offline", "error": str(e)}

    # App info
    services["webapp"] = {
        "status": "online",
        "hostname": socket.gethostname(),
        "version": "1.0.0",
        "environment": os.environ.get("APP_ENV", "development"),
        "uptime": time.strftime("%H:%M:%S", time.gmtime(time.time() - APP_START_TIME))
    }

    return jsonify(services)

@app.route("/api/latency-history")
def latency_history():
    """Retourne l'historique des latences pour les graphiques"""
    r = get_redis()
    history = r.lrange("latency_history", 0, 59)
    return jsonify([float(x) for x in history] if history else [])

APP_START_TIME = time.time()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

@app.route("/api/lb-status")
def lb_status():
    """Check health of both webapp instances directly"""
    import urllib.request
    results = {}
    for name, host in [("webapp-1", "webapp-1"), ("webapp-2", "webapp-2")]:
        try:
            req = urllib.request.urlopen(f"http://{host}:5000/health", timeout=2)
            results[name] = {"status": "online", "code": req.getcode()}
        except Exception as e:
            results[name] = {"status": "offline", "error": str(e)}
    results["current"] = socket.gethostname()
    return jsonify(results)
