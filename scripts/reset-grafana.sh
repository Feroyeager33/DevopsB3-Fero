#!/bin/bash
docker exec -u 0 grafana grafana-cli admin reset-password "Devops2026!"
echo "Mot de passe Grafana réinitialisé à Devops2026!"
