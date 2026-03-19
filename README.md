# 🚀 InfraLab – **Plateforme DevOps complète sur Azure**
# 📌 Description du projet
InfraLab est une plateforme DevOps complète déployée avec une approche cloud-native et orientée observabilité, sécurité et scalabilité.

Ce projet met en œuvre une infrastructure conteneurisée basée sur Docker et orchestrée via Docker Compose, intégrant :
  -  Une application web (Flask)
  -  Un reverse proxy (Nginx)
  -  Une base de données PostgreSQL avec réplication

Une stack de monitoring complète :
  -  Prometheus
  -  Grafana
  -  Loki
  -  Promtail
  -  Alertmanager

L’objectif est de simuler une infrastructure DevOps réaliste, prête pour un déploiement cloud (notamment sur Azure).

# ⚙️ Pré-requis

UBUNTU -> Version 24.04

DOCKER -> Version 29.3

DOCKER COMPOSE -> Version 5.1


# 🧱 Architecture

<img width="2718" height="1192" alt="image" src="https://github.com/user-attachments/assets/141f65c9-cb72-4506-ba9d-96dbf38bd32b" />


# 🛠️ Installation
1. Cloner le projet

`git clone https://github.com/ton-username/infralab.git`

`cd infralab`

2. Lancer l’infrastructure

`docker-compose up -d --build`

3. Vérifier les services

`docker ps`

### **⚠️ Problèmes possibles**

❌ Ports déjà utilisés → modifier les ports dans docker-compose.yml

❌ Ouvrir les ports sur Azure

❌ Permissions fichiers → ` chmod -R 755 `


# ▶️ Utilisation
### **📊 Monitoring** 
Prometheus collecte les métriques
Grafana affiche les dashboards
Loki + Promtail gèrent les logs
Alertmanager gère les alertes


# 👥 Contributeurs
**Ferhat Bayrak – Abdessamad Maklhoufi - Mondi Xharda - Aimé Désyre Mbadinga** 


# 🔗 Ressources utiles
Documentation Docker : 

https://docs.docker.com/

Documentation Terraform : 

https://developer.hashicorp.com/terraform
