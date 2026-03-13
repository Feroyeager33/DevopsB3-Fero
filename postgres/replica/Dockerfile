FROM postgres:16-alpine

LABEL maintainer="Mondi XHARDA"
LABEL description="PostgreSQL replica en streaming replication"

COPY setup-replica.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/setup-replica.sh

HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD pg_isready -U ${POSTGRES_USER:-infralab_user} || exit 1

EXPOSE 5432
