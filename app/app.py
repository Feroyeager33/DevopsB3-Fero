import os
import socket
import datetime
import psycopg2
import redis
from flask import Flask, render_template, jsonify
from prometheus_flask_instrumentator import Instrumentator

app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY", "dev-secret-key")

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

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
        result["primary"] = {"is_replica": row[0], "timestamp": str(row[1]), "status": "ok"}
        cur.close()
        conn.close()
    except Exception as e:
        result["primary"]["status"] = f"error: {str(e)}"
    try:
        conn = get_db_replica()
        cur = conn.cursor()
        cur.execute("SELECT pg_is_in_recovery(), current_timestamp")
        row = cur.fetchone()
        result["replica"] = {"is_replica": row[0], "timestamp": str(row[1]), "status": "ok"}
        cur.close()
        conn.close()
    except Exception as e:
        result["replica"]["status"] = f"error: {str(e)}"
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
