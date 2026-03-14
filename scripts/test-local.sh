#!/bin/bash
# ============================================
# InfraLab - Script de tests automatisés
# Usage : bash scripts/test-local.sh
# ============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
BASE_URL="http://localhost"

test_result() {
    local exit_code=$1
    local label=$2
    if [ "$exit_code" -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC} — $label"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}❌ FAIL${NC} — $label"
        FAIL=$((FAIL + 1))
    fi
}

run_test() {
    local label=$1
    shift
    "$@" > /dev/null 2>&1
    test_result $? "$label"
}

echo -e "${YELLOW}============================================${NC}"
echo -e "${YELLOW}   InfraLab - Tests automatisés             ${NC}"
echo -e "${YELLOW}============================================${NC}"
echo ""

# --- SECTION 1 : Services Docker ---
echo "📦 [1/5] Services Docker"

RUNNING=$(docker compose ps 2>/dev/null | grep -c "Up" || echo "0")
[ "$RUNNING" -ge 13 ]
test_result $? "Au moins 13 conteneurs running ($RUNNING détectés)"

docker compose ps | grep -q "postgres-primary.*healthy" ; test_result $? "postgres-primary est healthy"
docker compose ps | grep -q "redis.*healthy"            ; test_result $? "redis est healthy"
docker compose ps | grep -q "webapp-1.*healthy"         ; test_result $? "webapp-1 est healthy"
docker compose ps | grep -q "webapp-2.*healthy"         ; test_result $? "webapp-2 est healthy"

echo ""
echo "🌐 [2/5] Application Web"

curl -sf "${BASE_URL}/" | grep -q "InfraLab" ; test_result $? "Page d'accueil accessible"

STATUS=$(curl -s "${BASE_URL}/health" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "error")
[ "$STATUS" = "healthy" ] ; test_result $? "Healthcheck retourne 'healthy' (actuel: $STATUS)"

PG=$(curl -s "${BASE_URL}/health" | python3 -c "import sys,json; print(json.load(sys.stdin)['checks']['postgres_primary'])" 2>/dev/null || echo "error")
[ "$PG" = "ok" ] ; test_result $? "PostgreSQL connecté depuis l'app"

RD=$(curl -s "${BASE_URL}/health" | python3 -c "import sys,json; print(json.load(sys.stdin)['checks']['redis'])" 2>/dev/null || echo "error")
[ "$RD" = "ok" ] ; test_result $? "Redis connecté depuis l'app"

echo ""
echo "⚖️  [3/5] Load Balancing"

H1=$(curl -s "${BASE_URL}/api/info" | python3 -c "import sys,json; print(json.load(sys.stdin)['hostname'])" 2>/dev/null || echo "h1")
H2=$(curl -s "${BASE_URL}/api/info" | python3 -c "import sys,json; print(json.load(sys.stdin)['hostname'])" 2>/dev/null || echo "h2")
H3=$(curl -s "${BASE_URL}/api/info" | python3 -c "import sys,json; print(json.load(sys.stdin)['hostname'])" 2>/dev/null || echo "h3")
[ "$H1" != "$H2" ] || [ "$H1" != "$H3" ]
test_result $? "Load balancing actif (hostnames: $H1 / $H2 / $H3)"

echo ""
echo "🗄️  [4/5] Base de données"

IS_PRIMARY=$(curl -s "${BASE_URL}/api/db-status" | python3 -c "import sys,json; print(json.load(sys.stdin)['primary']['is_replica'])" 2>/dev/null || echo "error")
[ "$IS_PRIMARY" = "False" ] ; test_result $? "PostgreSQL primary est le master (is_replica=False)"

IS_REPLICA=$(curl -s "${BASE_URL}/api/db-status" | python3 -c "import sys,json; print(json.load(sys.stdin)['replica']['is_replica'])" 2>/dev/null || echo "error")
[ "$IS_REPLICA" = "True" ] ; test_result $? "PostgreSQL replica est en standby (is_replica=True)"

docker exec redis redis-cli -a "RedisPass789!" PING 2>/dev/null | grep -q "PONG"
test_result $? "Redis répond PONG"

echo ""
echo "📊 [5/5] Monitoring"

curl -sf "${BASE_URL}/prometheus/-/ready" > /dev/null 2>&1 ; test_result $? "Prometheus est ready"

GRAFANA=$(curl -s "${BASE_URL}/grafana/api/health" | python3 -c "import sys,json; print(json.load(sys.stdin)['database'])" 2>/dev/null || echo "error")
[ "$GRAFANA" = "ok" ] ; test_result $? "Grafana database est ok"

curl -sf "http://localhost:9000/" > /dev/null 2>&1 ; test_result $? "Authentik est accessible (port 9000)"

docker compose ps | grep -q "cadvisor.*healthy" ; test_result $? "cAdvisor est healthy"

# --- Résumé final ---
echo ""
echo -e "${YELLOW}============================================${NC}"
TOTAL=$((PASS + FAIL))
if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}🎉 $PASS/$TOTAL tests passés — Infrastructure 100% opérationnelle !${NC}"
else
    echo -e "${RED}⚠️  $PASS/$TOTAL tests passés — $FAIL échec(s) à corriger${NC}"
fi
echo -e "${YELLOW}============================================${NC}"
