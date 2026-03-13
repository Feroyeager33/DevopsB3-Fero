FROM postgres:16-alpine

LABEL maintainer="Mondi XHARDA"
LABEL description="PostgreSQL primary avec streaming replication"

COPY init.sql /docker-entrypoint-initdb.d/
COPY init-hba.sh /docker-entrypoint-initdb.d/02-init-hba.sh

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD pg_isready -U ${POSTGRES_USER:-infralab_user} -d ${POSTGRES_DB:-infralab} || exit 1

EXPOSE 5432
