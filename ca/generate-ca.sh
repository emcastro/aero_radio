#!/bin/bash
set -euo pipefail

CA_DIR="$(cd "$(dirname "$0")" && pwd)"
PRIVATE_DIR="$CA_DIR/private"

if [ -f "$PRIVATE_DIR/ca-key.pem" ]; then
    echo "CA already exists at $CA_DIR/ca.pem"
    exit 0
fi

echo "Generating CA key and certificate..."

mkdir -p "$PRIVATE_DIR" "$CA_DIR/issued"

# CA key
openssl genrsa -out "$PRIVATE_DIR/ca-key.pem" 4096

# Self-signed CA certificate
openssl req -x509 -new -nodes \
    -key "$PRIVATE_DIR/ca-key.pem" \
    -sha256 -days 3650 \
    -config "$CA_DIR/openssl-ca.conf" \
    -out "$CA_DIR/ca.pem"

# Initialize serial and index
echo "01" > "$PRIVATE_DIR/serial"
touch "$PRIVATE_DIR/index.txt"

chmod 600 "$PRIVATE_DIR/ca-key.pem"

echo "CA created:"
echo "  Certificate: $CA_DIR/ca.pem"
echo "  Key (DO NOT SHARE): $PRIVATE_DIR/ca-key.pem"
