# AeroRadio2

MQTT-based IoT messaging system with RabbitMQ, mutual TLS authentication, and a FastAPI auth backend.

## Quick Start

```bash
./scripts/setup-dev.sh
```

## Services (dev only, `network_mode: host`)

| Service  | Ports | Auth |
|----------|-------|------|
| RabbitMQ | 1883 (MQTT debug), 8883 (MQTTS mTLS), 5672 (AMQP), 15672 (mgmt UI) | mTLS + HTTP auth backend |
| Auth API | 8000 (localhost) | API key (query param) |

## Management UI

http://localhost:15672 — default credentials: `admin` / `admin`

## Adding a Device

```bash
./ca/generate-device-cert.sh <device-id>
```

Then add the device to `auth/src/auth_backend.py` in the `DEVICES` dict.

## Commands

```bash
# Build and start
podman-compose build && podman-compose up -d

# Rebuild auth after changes
make rebuild-auth

# Rebuild rabbitmq after changes
make rebuild-rabbitmq

# Logs
make logs

# Stop
podman-compose stop

# Destroy
podman-compose down
```

## Testing

```bash
# Quick MQTT connect test
make test-connect

# Subscribe to commands topic
make test-subscribe

# Publish telemetry message
make test-publish

# Direct HTTP test of all 4 auth endpoints
make test-auth

# Run all of the above
make test-all
```

Individual test scripts in `tests/` can also be run directly:

```bash
uv run python3 tests/test_auth.py
```

## E2E MQTT Test

```bash
mosquitto_pub \
  --cafile ca/ca.pem \
  --cert ca/issued/device-test-001.pem \
  --key ca/issued/device-test-001-key.pem \
  -h localhost -p 8883 \
  -t devices/device-test-001/telemetry/temp \
  -m '{"value":24}' \
  -u device-test-001 -P device-test-001 \
  -d
```

**Important:** The MQTT CONNECT packet must include a non-empty password matching the device ID. Despite `ssl_cert_login=true` authenticating via the client certificate CN, RabbitMQ's MQTT plugin still requires a password field in the CONNECT packet. Empty password results in `"no password provided"` and CONNACK code 4.

## Critical: Auth Backend Response Format

RabbitMQ's `rabbitmq_auth_backend_http` expects **plain text** responses (not JSON):
- `/auth/user`: return `"allow administrator"` (valid user with management tag), `"allow"`, or `"deny"`
- `/auth/vhost`, `/auth/resource`, `/auth/topic`: return `"allow"` or `"deny"`

Set `response_class=PlainTextResponse` on FastAPI endpoints. JSON responses like `{"authenticated": true}` will cause connection rejection (CONNACK code 4).

## Auth API Key

Set `AUTH_API_KEY` via environment variable (`AUTH_API_KEY=mykey ./scripts/setup-dev.sh`). Defaults to `changeme` in `podman-compose.yml`. RabbitMQ's `rabbitmq.conf` hardcodes the value (Cuttlefish does not expand env vars). The auth service reads it from `AUTH_API_KEY` env var in its config (`src/config.py`).

## Topic Auth: Dot / Slash Conversion

RabbitMQ MQTT internally converts topic separator `/` to `.` when passing routing keys to the HTTP auth backend. For example, an MQTT subscribe to `devices/device-test-001/commands/#` reaches `/auth/topic` as:

```
routing_key = devices.device-test-001.commands.#
```

The auth backend's `check_topic_access` reverses this (`"."` → `"/"`) before matching against device patterns stored with `/` separators.

## Project Layout

```
Makefile             Build + test targets
ca/                  OpenSSL CA + device certificate scripts
rabbitmq/            Dockerfile + config + server TLS certs
auth/                FastAPI auth backend service
tests/               MQTT + HTTP test scripts
scripts/             setup script
docs/                architecture documentation
```
