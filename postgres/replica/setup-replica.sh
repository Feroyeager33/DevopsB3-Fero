#!/bin/bash
set -e

echo "Attente du PostgreSQL primary..."
until pg_isready -h postgres-primary -p 5432 -U ${POSTGRES_USER}; do
    echo "Primary pas encore prêt, attente 2s..."
    sleep 2
done
echo "Primary est prêt !"

pg_ctl stop -D "$PGDATA" -m fast || true
rm -rf "$PGDATA"/*

echo "Base backup depuis le primary..."
PGPASSWORD=${POSTGRES_REPLICATION_PASSWORD} pg_basebackup \
    -h postgres-primary \
    -p 5432 \
    -U replicator \
    -D "$PGDATA" \
    -Fp -Xs -P -R

echo "Configuration du replica terminée !"
echo "Démarrage en mode standby..."
pg_ctl start -D "$PGDATA"
