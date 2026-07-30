#!/bin/sh
set -e

cd /app/auth/src
while true; do
    /app/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-dir . || true
    echo "uvicorn exited with $?, restarting..."
done &

# shellcheck disable=SC2034
for i in $(seq 1 15); do
    # We use Python instead of wget/curl: BusyBox wget lacks --post-data, 
    # curl not in base image, Python is already installed
    if python3 -c "
import urllib.request
urllib.request.urlopen(
    'http://127.0.0.1:8000/auth/user',
    b'username=health',
)
" 2>/dev/null; then
        break
    fi
    sleep 1
done
echo "auth backend health check complete"

exec /opt/rabbitmq/sbin/rabbitmq-server
