-- Créer la base pour Authentik
CREATE DATABASE authentik;

-- Créer le rôle de réplication
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'replicator') THEN
        CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'ReplPass456!';
    END IF;
END
$$;

-- Table de démo
CREATE TABLE IF NOT EXISTS visits (
    id SERIAL PRIMARY KEY,
    hostname VARCHAR(255),
    visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO infralab_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO infralab_user;
