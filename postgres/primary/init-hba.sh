#!/bin/bash
# Autoriser les connexions de réplication depuis n'importe quel host
echo "host replication replicator 0.0.0.0/0 md5" >> "${PGDATA}/pg_hba.conf"
echo "✅ pg_hba.conf mis à jour pour la réplication"
