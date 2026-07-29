FROM docker.io/library/rabbitmq:4.1-management-alpine

COPY enabled_plugins /etc/rabbitmq/enabled_plugins
COPY rabbitmq.conf /etc/rabbitmq/rabbitmq.conf

COPY tls/ca.pem         /etc/rabbitmq/tls/ca.pem
COPY tls/server.pem     /etc/rabbitmq/tls/server.pem
COPY tls/server-key.pem /etc/rabbitmq/tls/server-key.pem

RUN chmod 600 /etc/rabbitmq/tls/server-key.pem && \
    chown -R rabbitmq:rabbitmq /etc/rabbitmq/tls
