.PHONY: up down rebuild logs \
        test-connect test-subscribe test-publish test-auth test-all

up:
	podman-compose up -d

down:
	podman-compose down

rebuild:
	podman-compose build && podman-compose down && podman-compose up -d

logs:
	podman-compose logs -f

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
