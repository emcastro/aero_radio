.PHONY: up down rebuild logs sync-deps \
        test-connect test-subscribe test-publish test-auth test-all \
        run-iot run-central run-central-amqp

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

sync-deps:
	uv lock && uv export --locked --format requirements-txt -o auth/requirements.txt

# Run

run-iot:
	uv run python -u clients/iot_simulator.py

run-central:
	uv run python -u clients/central.py

run-central-amqp:
	uv run python -u clients/central_amqp.py

# Tests

test-connect:
	uv run python tests/test_connect.py

test-subscribe:
	uv run python tests/test_subscribe.py

test-publish:
	uv run python tests/test_publish.py

test-auth:
	uv run python tests/test_auth.py

test-all: test-connect test-subscribe test-publish test-auth
	@echo 'All tests: PASS'
