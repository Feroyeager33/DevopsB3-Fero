#!/bin/bash

# Couleurs pour le terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🐒 Démarrage du Chaos Monkey sur Infralab...${NC}"

while true; do
  # Choisir aléatoirement entre webapp-1 et webapp-2
  TARGET="webapp-$(( ( RANDOM % 2 ) + 1 ))"
  
  echo -e "${RED}🔥 [ATTACK] Chaos Monkey arrête : $TARGET${NC}"
  docker stop $TARGET > /dev/null
  
  echo -e "${YELLOW}⏳ Vérification de la résilience pendant 20 secondes...${NC}"
  # C'est ici que tu dois rafraîchir ta page web pour voir si ça marche encore !
  sleep 20
  
  echo -e "${GREEN}🏥 [REPAIR] Auto-healing : Redémarrage de $TARGET...${NC}"
  docker start $TARGET > /dev/null
  
  echo -e "${NC}✅ Système rétabli. Repos de 40 secondes avant le prochain chaos."
  sleep 40
done
