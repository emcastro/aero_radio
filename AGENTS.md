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
podman-compose build auth && podman-compose up -d auth

# Logs
podman-compose logs -f

# Stop
podman-compose stop

# Destroy
podman-compose down
```

## Quick MQTT Test

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

## Critical: Auth Backend Response Format

RabbitMQ's `rabbitmq_auth_backend_http` expects **plain text** responses (not JSON):
- `/auth/user`: return `"allow administrator"` (valid user with management tag), `"allow"`, or `"deny"`
- `/auth/vhost`, `/auth/resource`, `/auth/topic`: return `"allow"` or `"deny"`

Set `response_class=PlainTextResponse` on FastAPI endpoints. JSON responses like `{"authenticated": true}` will cause connection rejection (CONNACK code 4).

## Auth API Key

Set `AUTH_API_KEY` via environment variable (`AUTH_API_KEY=mykey ./scripts/setup-dev.sh`). Defaults to `changeme` in `podman-compose.yml`. RabbitMQ's `rabbitmq.conf` hardcodes the value (Cuttlefish does not expand env vars). The auth service reads it from `AUTH_API_KEY` env var in its config (`src/config.py`).

## Project Layout

```
ca/                  OpenSSL CA + device certificate scripts
rabbitmq/            Dockerfile + config + server TLS certs
auth/                FastAPI auth backend service
scripts/             setup script
docs/                architecture documentation
```
