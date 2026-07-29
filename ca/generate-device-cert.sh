#!/bin/bash
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <device-id> [password]"
    exit 1
fi

DEVICE_ID="$1"
PASSWORD="${2:-}"

CA_DIR="$(cd "$(dirname "$0")" && pwd)"
PRIVATE_DIR="$CA_DIR/private"
ISSUED_DIR="$CA_DIR/issued"

if [ ! -f "$PRIVATE_DIR/ca-key.pem" ]; then
    echo "Error: CA not found. Run ./generate-ca.sh first."
    exit 1
fi

echo "Generating certificate for device: $DEVICE_ID"

cd "$CA_DIR"

# Device key
openssl genrsa -out "$ISSUED_DIR/$DEVICE_ID-key.pem" 2048

# Device CSR
openssl req -new \
    -key "$ISSUED_DIR/$DEVICE_ID-key.pem" \
    -out "$ISSUED_DIR/$DEVICE_ID.csr" \
    -subj "/CN=$DEVICE_ID"

# Sign with CA
openssl ca -batch \
    -config "$CA_DIR/openssl-ca.conf" \
    -extensions device_cert \
    -in "$ISSUED_DIR/$DEVICE_ID.csr" \
    -out "$ISSUED_DIR/$DEVICE_ID.pem"

# Cleanup CSR
rm -f "$ISSUED_DIR/$DEVICE_ID.csr"

chmod 600 "$ISSUED_DIR/$DEVICE_ID-key.pem"

if [ -n "$PASSWORD" ]; then
    openssl pkcs12 -export \
        -in "$ISSUED_DIR/$DEVICE_ID.pem" \
        -inkey "$ISSUED_DIR/$DEVICE_ID-key.pem" \
        -certfile "$CA_DIR/ca.pem" \
        -out "$ISSUED_DIR/$DEVICE_ID.p12" \
        -passout "pass:$PASSWORD"
    echo "  PKCS#12 bundle: $ISSUED_DIR/$DEVICE_ID.p12 (password: $PASSWORD)"
fi

echo "Device certificate created:"
echo "  Certificate: $ISSUED_DIR/$DEVICE_ID.pem"
echo "  Key:         $ISSUED_DIR/$DEVICE_ID-key.pem"
echo "  CA:          $CA_DIR/ca.pem"
echo ""
echo "Upload to SIM7600 with:"
echo "  AT+CCERTDOWN=0,\"$DEVICE_ID.pem\",<size>,<crc16>"
echo "  AT+CCERTDOWN=1,\"$DEVICE_ID-key.pem\",<size>,<crc16>"
echo "  AT+CCERTDOWN=2,\"ca.pem\",<size>,<crc16>"
