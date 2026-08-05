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

Only the internal `admin` user has access. HTTP-authenticated MQTT/AMQP users
get no management tag (`/auth/user` returns plain `"allow"`, not
`"allow administrator"`).

## Adding a Device

```bash
./ca/generate-device-cert.sh <device-id>
```

That's it — there is **no device registry**. Any certificate signed by the
project CA authenticates over MQTT. To revoke a device temporarily, feed its CN
to the auth backend's in-memory revocation list (lost on restart):

```bash
curl -X POST http://localhost:8000/auth/revoke -d 'cn=device-test-001'
curl -X POST http://localhost:8000/auth/unrevoke -d 'cn=device-test-001'
```

Connections from a revoked CN are refused immediately. External processes can
also call these endpoints to maintain the list.

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
# Quick MQTT connect test (mTLS, paho-mqtt)
make test-connect

# Subscribe to commands topic (paho-mqtt)
make test-subscribe

# End-to-end MQTT round trip: device publishes telemetry, central receives it
make test-publish

# Cross-protocol round trip: MQTT publish received via AMQP (pika)
make test-amqp

# Direct HTTP test of all 4 auth endpoints
make test-auth

# Run all of the above
make test-all
```

> **Note:** The MQTT tests hardcode device IDs, certificates and topic names
> (`devices/<device>/telemetry/#`, `devices/<device>/commands/#`, …) that must
> match the certificates in `ca/issued/`. Topic names and device IDs **will
> change** — when they do, update these in sync:
> `tests/test_connect.py`, `tests/test_subscribe.py`, `tests/test_publish.py`,
> `tests/test_amqp.py`, and the `clients/` scripts.

> **Note:** The tests assume no other MQTT clients are active. `make run-iot`
> (publishes on `devices/device-test-001/telemetry/value`) and `make run-central`
> share client IDs and topics with the tests, so running them concurrently can
> cause false failures. Stop those processes before `make test-all`.

Individual test scripts in `tests/` can also be run directly:

```bash
uv run python3 tests/test_auth.py
```

## Auth API Debug

The auth backend listens on `0.0.0.0:8000` for dev debugging. Test directly:

```bash
curl -X POST http://localhost:8000/auth/user \
  -d 'username=device-test-001&client_id=device-test-001'
```

The request above mirrors a cert-authenticated MQTT login: **no password field**
(RabbitMQ drops it — the MQTT plugin excludes the password when it is the
`none` sentinel for certificate logins). An AMQP service login is tested with
a password and no `client_id`:

```bash
curl -X POST http://localhost:8000/auth/user -d 'username=central&password=central'
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
  -d
```

**Important:** MQTT authenticates **by certificate only**. With
`ssl_cert_login=true`, RabbitMQ derives the auth username from the client
certificate CN and calls `/auth/user` **without a password field** (the MQTT
plugin drops it). The CONNECT packet must therefore **not** carry a
username/password:

- A certificate signed by the project CA authenticates as its CN — there is
  no device registry.
- A CN on the auth backend's in-memory revocation list (fed via
  `POST /auth/revoke`) is refused.
- If a client sends username/password anyway, it is **refused**: RabbitMQ would
  otherwise let the CONNECT credentials take priority over the certificate CN,
  letting any certificate holder impersonate another device.

AMQP service connections (no `client_id`) authenticate with
username/password against `SERVICE_ACCOUNTS` in `auth/src/auth_backend.py`
(e.g. `central` / `central`).

## Clients

Two Python client scripts are provided in `clients/`:

| Script | Device | Role |
|--------|--------|------|
| `clients/iot_simulator.py` | `device-test-001` | Publishes ramp 0..100 then 100..0 every 0.5s on `devices/device-test-001/telemetry/value` |
| `clients/central.py` | `central` | Subscribes to `devices/+/telemetry/#` and prints all received messages |
| `clients/central_amqp.py` | `central` | Same as central.py but via AMQP (port 5672) using `pika` |

Both MQTT clients connect via MQTTS (port 8883) with mTLS using `paho-mqtt` and
`CallbackAPIVersion.VERSION2`, **without** username/password (certificate-only).
`central_amqp.py` connects via AMQP (port 5672) with `central` / `central`.

Before running `central`, generate its certificate:

```bash
./ca/generate-device-cert.sh central
```

### AMQP vs MQTT for the central consumer

`central_amqp.py` uses RabbitMQ's native AMQP protocol (port 5672) instead of MQTTS. The IoT device publishes via MQTT, RabbitMQ routes internally to `amq.topic`, and the AMQP consumer binds with routing key `devices.#`.

| Aspect | MQTT (`central.py`) | AMQP (`central_amqp.py`) |
|--------|---------------------|--------------------------|
| Port | 8883 (MQTTS, mTLS) | 5672 (AMQP, plain) |
| Auth | Client certificate only | Username/password (PLAIN) |
| Reliability | QoS 0/1/2, no app-level ACK | Manual ACK, prefetch, durable queues |
| Routing | Subscribe topic `devices/+/telemetry/#` | Bind to `amq.topic` with `devices.#` |
| Code | Simpler (subscribe + loop) | More boilerplate (queue + bind + consume) |
| Deps | `paho-mqtt` | `pika` |

**Advantages of AMQP:** manual ACKs, durable queues survive restarts, richer protocol features, no mTLS overhead.

**Disadvantages:** more code, plain password on the wire (no TLS on 5672), additional dependency (`pika`).

## Critical: Auth Backend Response Format

RabbitMQ's `rabbitmq_auth_backend_http` expects **plain text** responses (not JSON):
- `/auth/user`: return `"allow"` or `"deny"`
- `/auth/vhost`, `/auth/resource`, `/auth/topic`: return `"allow"` or `"deny"`

## Topic Auth

MQTT topic access is **permissive**: any certificate-authenticated device may
use any topic (`/auth/topic` always returns `"allow"`). If per-device topic
isolation is needed later, note that RabbitMQ converts MQTT `/` to `.` when
passing routing keys (e.g. `devices/device-test-001/commands/#` arrives as
`devices.device-test-001.commands.#`); reverse it before matching.

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
