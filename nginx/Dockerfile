FROM nginx:1.25-alpine

LABEL maintainer="Mondi XHARDA"
LABEL description="Nginx reverse proxy avec load balancing pour InfraLab"

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/

RUN mkdir -p /var/cache/nginx /var/log/nginx && \
    chown -R nginx:nginx /var/cache/nginx /var/log/nginx

EXPOSE 80 443

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/nginx-health || exit 1

CMD ["nginx", "-g", "daemon off;"]
