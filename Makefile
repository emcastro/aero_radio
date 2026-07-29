.PHONY: up down rebuild-auth rebuild-rabbitmq logs \
        logs-auth logs-rabbitmq \
        test-connect test-subscribe test-publish test-auth test-all

up:
	podman-compose up -d

down:
	podman-compose down

rebuild-auth:
	podman build -t aero_radio_auth -f auth/Dockerfile auth/ && \
	podman-compose down && podman-compose up -d

rebuild-rabbitmq:
	podman build -t aero_radio_rabbitmq -f rabbitmq/Dockerfile rabbitmq/ && \
	podman-compose down && podman-compose up -d

logs:
	podman-compose logs -f

logs-auth:
	podman logs -f aero-auth

logs-rabbitmq:
	podman logs -f aero-rabbitmq

test-connect:
	uv run python3 tests/test_connect.py

test-subscribe:
	uv run python3 tests/test_subscribe.py

test-publish:
	uv run python3 tests/test_publish.py

test-auth:
	uv run python3 tests/test_auth.py

test-all: test-connect test-subscribe test-publish test-auth
	@echo 'All tests: PASS'
