FROM docker.io/library/rabbitmq:4.1-management-alpine

RUN NO_PROXY=* apk add --no-cache python3 py3-pip

RUN python3 -m venv /app/venv

COPY auth/requirements.txt /tmp/requirements.txt
RUN NO_PROXY=* /app/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

COPY rabbitmq/enabled_plugins /etc/rabbitmq/enabled_plugins
COPY rabbitmq/rabbitmq.conf /etc/rabbitmq/rabbitmq.conf
COPY rabbitmq/tls/ /etc/rabbitmq/tls/

RUN chmod 600 /etc/rabbitmq/tls/server-key.pem && \
    chown -R rabbitmq:rabbitmq /etc/rabbitmq/tls

COPY auth/src/ /app/auth/src/

COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

EXPOSE 1883 8883 5672 15672 8000

CMD ["/docker-entrypoint.sh"]
