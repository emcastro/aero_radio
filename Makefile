.PHONY: up down rebuild logs sync-deps typecheck lint \
        test-unit test-connect test-subscribe test-publish test-amqp test-auth test-all \
        run-iot run-central run-central-amqp \
        download-ogn clean-ogn download-adsb download-all

up:
	podman-compose up -d

down:
	podman-compose down

rebuild:
	podman-compose build && podman-compose down && podman-compose up -d

logs:
	podman-compose logs -f

sync-deps:
	uv lock && uv export --locked --no-dev --format requirements-txt -o auth/requirements.txt

typecheck:
	uv run pyright

lint:
	uv run pylint .

# Run

run-iot:
	uv run python -u clients/iot_simulator.py

run-central:
	uv run python -u clients/central.py

run-central-amqp:
	uv run python -u clients/central_amqp.py

# Tests

test-unit:
	uv run pytest -v

test-connect:
	uv run python tests_integ/test_connect.py

test-subscribe:
	uv run python tests_integ/test_subscribe.py

test-publish:
	uv run python tests_integ/test_publish.py

test-amqp:
	uv run python tests_integ/test_amqp.py

test-auth:
	uv run python tests_integ/test_auth.py

test-all: test-unit test-connect test-subscribe test-publish test-amqp test-auth
	@echo 'All tests: PASS'

# OGN data pipeline: phase 1 (slow, real-time stream) then phase 2 (DuckDB, ~3s).

download-ogn:
	scripts/download_ogn.sh

download-adsb:
	scripts/download_adsb.sh

download-all:
	scripts/download_all.sh

clean-ogn:
	scripts/clean_ogn.sh
