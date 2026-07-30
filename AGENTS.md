# AeroRadio2

> Ne pas commiter sans ordre exprès de l'utilisateur.

MQTT-based IoT messaging system with RabbitMQ, mutual TLS authentication, and a FastAPI auth backend.

## Quick Start

```bash
./scripts/setup-dev.sh
```

## Architecture

Single container (`aero-rabbitmq`) running both RabbitMQ and the FastAPI auth backend. For dev only, uses `network_mode: host`.

```
┌────────────────────────────────────┐
│  Container: aero-rabbitmq          │
│                                    │
│  ┌──────────┐  HTTP 127.0.0.1:8000 │
│  │ RabbitMQ │────────────────┐     │
│  │ (5672,   │                │     │
│  │  15672)  │                ▼     │
│  │          │           ┌────────┐ │
│  │  8883 MQTTS mTLS     │ Auth   │ │
│  │  1883 MQTT debug     │ FastAPI│ │
│  └──────────┘           └────────┘ │
└────────────────────────────────────┘
```

| Port | Purpose | Dev access |
|------|---------|------------|
| 1883 | MQTT (TCP, debug) | localhost |
| 8883 | MQTTS (mTLS, devices) | localhost |
| 5672 | AMQP (consumers) | localhost |
| 15672 | Management UI (admin/admin) | localhost |
| 8000 | Auth API (dev debug only) | localhost |

## Volume Mounts (live edit)

All config and Python code is mounted from the host — no rebuild needed for changes:

| Host path | Container path |
|-----------|----------------|
| `rabbitmq/rabbitmq.conf` | `/etc/rabbitmq/rabbitmq.conf` |
| `rabbitmq/enabled_plugins` | `/etc/rabbitmq/enabled_plugins` |
| `rabbitmq/tls/` | `/etc/rabbitmq/tls/` |
| `auth/src/` | `/app/auth/src/` |

The Dockerfile `COPY` exists so the image is self-contained; the volumes above **override** those baked-in files at runtime. This means you can `podman run` without volumes and it still works — the mounts are a dev convenience, not a requirement.

After editing code or config, just restart the container:

```bash
podman-compose restart
```

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
make up

# Rebuild and restart (e.g. after new pip deps)
make rebuild

# Logs
make logs

# RabbitMQ logs only
make logs-rabbitmq

# Sync Python deps (regenerate uv.lock + requirements.txt)
make sync-deps

# Run clients (two terminals)
make run-central    # central process, subscribes to devices/+/telemetry/#
make run-iot        # IoT simulator, publishes 0..100..0

# Or use AMQP for the central consumer
make run-central-amqp

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

## Auth API Debug

The auth backend listens on `0.0.0.0:8000` for dev debugging. Test directly:

```bash
curl -X POST http://localhost:8000/auth/user \
  -d 'username=device-test-001&password='
```

**Do not expose port 8000 in production.** The auth backend is intended for internal use by RabbitMQ only.

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

## Clients

Two Python client scripts are provided in `clients/`:

| Script | Device | Role |
|--------|--------|------|
| `clients/iot_simulator.py` | `device-test-001` | Publishes ramp 0..100 then 100..0 every 0.5s on `devices/device-test-001/telemetry/value` |
| `clients/central.py` | `central` | Subscribes to `devices/+/telemetry/#` and prints all received messages |
| `clients/central_amqp.py` | `central` | Same as central.py but via AMQP (port 5672) using `pika` |

Both connect via MQTTS (port 8883) with mTLS using `paho-mqtt` and `CallbackAPIVersion.VERSION2`.

Before running `central`, generate its certificate:

```bash
./ca/generate-device-cert.sh central
```

Then add it to `auth/src/auth_backend.py`.

### AMQP vs MQTT for the central consumer

`central_amqp.py` uses RabbitMQ's native AMQP protocol (port 5672) instead of MQTTS. The IoT device publishes via MQTT, RabbitMQ routes internally to `amq.topic`, and the AMQP consumer binds with routing key `devices.#`.

| Aspect | MQTT (`central.py`) | AMQP (`central_amqp.py`) |
|--------|---------------------|--------------------------|
| Port | 8883 (MQTTS, mTLS) | 5672 (AMQP, plain) |
| Auth | Client certificate + password | Username/password (PLAIN) |
| Reliability | QoS 0/1/2, no app-level ACK | Manual ACK, prefetch, durable queues |
| Routing | Subscribe topic `devices/+/telemetry/#` | Bind to `amq.topic` with `devices.#` |
| Code | Simpler (subscribe + loop) | More boilerplate (queue + bind + consume) |
| Deps | `paho-mqtt` | `pika` |

**Advantages of AMQP:** manual ACKs, durable queues survive restarts, richer protocol features, no mTLS overhead.

**Disadvantages:** more code, plain password on the wire (no TLS on 5672), additional dependency (`pika`).

## Critical: Auth Backend Response Format

RabbitMQ's `rabbitmq_auth_backend_http` expects **plain text** responses (not JSON):
- `/auth/user`: return `"allow administrator"` (valid user with management tag), `"allow"`, or `"deny"`
- `/auth/vhost`, `/auth/resource`, `/auth/topic`: return `"allow"` or `"deny"`

## Topic Auth: Dot / Slash Conversion

RabbitMQ MQTT internally converts topic separator `/` to `.` when passing routing keys to the HTTP auth backend. For example, an MQTT subscribe to `devices/device-test-001/commands/#` reaches `/auth/topic` as:

```
routing_key = devices.device-test-001.commands.#
```

The auth backend's `check_topic_access` reverses this (`"."` → `"/"`) before matching against device patterns stored with `/` separators.

## Project Layout

```
Dockerfile            Combined image (RabbitMQ + Python + auth)
docker-entrypoint.sh  Container entrypoint
Makefile              Build + test targets
ca/                   OpenSSL CA + device certificate scripts
rabbitmq/             RabbitMQ config + TLS certs
auth/                 FastAPI auth backend source code
tests/                MQTT + HTTP test scripts
clients/              Python client scripts (IoT simulator + central + central AMQP)
scripts/              Setup script
docs/                 Architecture documentation
```
