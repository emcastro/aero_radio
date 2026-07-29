# AeroRadio2 Architecture

## Overview

AeroRadio2 is an MQTT-based IoT messaging system built on RabbitMQ with mutual TLS authentication.
Device authentication is handled by X.509 client certificates, while topic authorization is
delegated via RabbitMQ's HTTP Auth Backend to a FastAPI service.

## Components

```
┌──────────────────────────────────────────────────────────────────┐
│                        Host (network_mode: host)                  │
│                                                                   │
│  ┌─────────────────────┐          ┌──────────────────────────┐    │
│  │      RabbitMQ        │  HTTP   │    FastAPI Auth Backend   │    │
│  │                      │◄────────│                          │    │
│  │  Ports:              │  auth   │  POST /auth/user          │    │
│  │  1883  MQTT (debug)  │          │  POST /auth/vhost        │    │
│  │  8883  MQTTS (mTLS)  │          │  POST /auth/resource     │    │
│  │  5672  AMQP          │          │  POST /auth/topic        │    │
│  │  15672 Management UI │          │  Port 8000 (127.0.0.1)   │    │
│  └──────────┬───────────┘          └──────────────────────────┘    │
│             │                                                      │
│             │ mQTTS :8883 (mTLS with client cert)                  │
│             │                                                      │
│  ┌──────────┴───────────┐                                         │
│  │  External Clients     │                                         │
│  │  (IoT devices via     │                                         │
│  │   SIM7600, consumers) │                                         │
│  └──────────────────────┘                                         │
└──────────────────────────────────────────────────────────────────┘
```

## Authentication Flow

1. **TLS Handshake** — IoT device connects to port 8883 presenting its client certificate.
2. **Certificate Validation** — RabbitMQ verifies the certificate against the CA (`ca.pem`).
   - If invalid → connection rejected.
3. **User Authentication** — RabbitMQ calls `POST /auth/user` with `username = CN` from the cert.
   - Auth service checks if CN exists in its device registry.
4. **Topic Authorization** — On each publish/subscribe, RabbitMQ calls `POST /auth/topic`.
   - Auth service verifies the routing_key matches the device's allowed topic patterns.

## Certificate Authority (CA)

The `ca/` directory contains an offline CA based on OpenSSL.

| Script | Purpose |
|--------|---------|
| `ca/generate-ca.sh` | Initialize the CA (root key + self-signed cert) |
| `ca/generate-device-cert.sh <id>` | Issue a client certificate for a device |

A device certificate's Common Name (CN) must match a key in the auth backend's `DEVICES` dict.

## Ports

| Port | Protocol | Service | Notes |
|------|----------|---------|-------|
| 1883 | MQTT     | RabbitMQ | TCP (debug only, remove in production) |
| 8883 | MQTTS    | RabbitMQ | mTLS required (device-facing) |
| 5672 | AMQP     | RabbitMQ | For external consumers |
| 15672| HTTP     | RabbitMQ | Management UI (admin/admin) |
| 8000 | HTTP     | Auth     | Internal auth backend (127.0.0.1 only) |

## Development Setup

```bash
./scripts/setup-dev.sh
```

This will:
1. Create the CA if missing
2. Generate the RabbitMQ server certificate signed by the CA
3. Generate a test device certificate (`device-test-001`)
4. Build and start containers with `podman-compose`

## Adding a Device

1. Generate a certificate:

   ```bash
   ./ca/generate-device-cert.sh my-device-42
   ```

2. Add an entry in `auth/src/auth_backend.py`:

   ```python
   DEVICES = {
       "my-device-42": {
           "description": "My new device",
           "topics": {
               "write": ["devices/my-device-42/telemetry/#"],
               "read":  ["devices/my-device-42/commands/#"],
           },
       },
   }
   ```

3. Copy `ca/issued/my-device-42.pem`, `ca/issued/my-device-42-key.pem`, and `ca/ca.pem` to the device.

## Future Work

- CA web service to issue device certificates on demand
- Persistent backend (e.g., PostgreSQL) for device registry instead of hardcoded dict
- Proper PKI with certificate revocation (CRL/OCSP)
- Remove port 1883 (TCP MQTT) in production
