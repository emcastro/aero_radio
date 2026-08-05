#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== AeroRadio2 Development Setup ==="
echo ""

# --- Prerequisites ---
echo "[1/5] Checking prerequisites..."
for cmd in openssl podman podman-compose; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: $cmd is required but not found. Install it first."
        exit 1
    fi
done
echo "  All prerequisites found."
echo ""

# --- Generate CA ---
echo "[2/5] Setting up Certificate Authority..."
cd "$ROOT/ca"
if [ ! -f private/ca-key.pem ]; then
    bash generate-ca.sh
else
    echo "  CA already exists, skipping."
fi
echo ""

# --- Generate server certificate ---
echo "[3/5] Generating RabbitMQ server certificate..."
cd "$ROOT/rabbitmq"
mkdir -p tls
if [ ! -f tls/server-key.pem ]; then
    # Server private key
    openssl genrsa -out tls/server-key.pem 2048

    # Server CSR
    openssl req -new \
        -key tls/server-key.pem \
        -out /tmp/server.csr \
        -subj "/CN=aero-rabbitmq"

    # Sign with CA (must be in CA dir for relative path to work)
    cd "$ROOT/ca"
    openssl ca -batch \
        -config openssl-ca.conf \
        -extensions server_cert \
        -in /tmp/server.csr \
        -out "$ROOT/rabbitmq/tls/server.pem"
    cd "$ROOT/rabbitmq"

    rm -f /tmp/server.csr
    chmod 600 tls/server-key.pem
    
    # Copy CA cert for RabbitMQ
    cp "$ROOT/ca/ca.pem" tls/ca.pem
    echo "  Server certificate created."
else
    echo "  Server certificate already exists, skipping."
fi
echo ""

# --- Generate test device certificates ---
echo "[4/5] Generating test device certificates..."
cd "$ROOT/ca"
for dev in device-test-001 device-test-002 device-revoked-001; do
    if [ ! -f "issued/$dev.pem" ]; then
        bash generate-device-cert.sh "$dev"
    else
        echo "  Certificate for $dev already exists, skipping."
    fi
done
echo ""

# --- Start services ---
echo "[5/5] Building and starting containers..."
cd "$ROOT"
podman-compose build
podman-compose up -d
echo ""

# --- Summary ---
echo "Setup complete!"
echo ""
echo "=== Service Endpoints (dev only - network_mode: host) ==="
echo "  MQTT (TCP debug):    localhost:1883"
echo "  MQTTS (mTLS):        localhost:8883"
echo "  AMQP:                localhost:5672"
echo "  Management UI:       http://localhost:15672  (admin/admin)"
echo "  Auth API (dev):      http://localhost:8000"
echo ""
echo "=== Test Device ==="
echo "  ID:   device-test-001"
echo "  Cert: ca/issued/device-test-001.pem"
echo "  Key:  ca/issued/device-test-001-key.pem"
echo ""
echo "=== Quick test ==="
echo "  mosquitto_pub --cafile ca/ca.pem --cert ca/issued/device-test-001.pem \\"
echo "    --key ca/issued/device-test-001-key.pem -h localhost -p 8883 \\"
echo "    -t devices/device-test-001/telemetry/temp -m '{\"value\":24}'"
echo ""
