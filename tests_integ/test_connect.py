import sys
import time
from urllib.request import Request, urlopen
from urllib.parse import urlencode

import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 8883
CA_CERT = "ca/ca.pem"
AUTH_BASE = "http://localhost:8000/auth"


def set_revoked(cn: str, revoked: bool) -> None:
    path = "revoke" if revoked else "unrevoke"
    body = urlencode({"cn": cn}).encode()
    urlopen(Request(f"{AUTH_BASE}/{path}", data=body)).read()


def connect(cert: str, key: str, client_id: str, username=None, password=None) -> int:
    result = {}

    def on_connect(client, userdata, flags, reason_code, properties=None):
        result["reason_code"] = reason_code
        client.disconnect()

    client = mqtt.Client(client_id=client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.tls_set(ca_certs=CA_CERT, certfile=cert, keyfile=key)
    client.tls_insecure_set(True)
    if username is not None:
        client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(BROKER, PORT, 60)
    client.loop_start()

    deadline = time.time() + 10
    while "reason_code" not in result and time.time() < deadline:
        time.sleep(0.1)

    client.loop_stop()
    return result.get("reason_code", -1)


# MQTT authenticates by certificate only: the CONNECT packet must NOT carry
# username/password. Any cert signed by the project CA works, unless its CN is
# on the in-memory revocation list (fed via POST /auth/revoke).
set_revoked("device-revoked-001", True)
code_revoked = connect(
    "ca/issued/device-revoked-001.pem", "ca/issued/device-revoked-001-key.pem",
    "device-revoked-001",
)
set_revoked("device-revoked-001", False)
code_unrevoked = connect(
    "ca/issued/device-revoked-001.pem", "ca/issued/device-revoked-001-key.pem",
    "device-revoked-001",
)

codes = {
    "cert-only device-test-001": connect(
        "ca/issued/device-test-001.pem", "ca/issued/device-test-001-key.pem",
        "device-test-001",
    ),
    "cert-only device-test-002": connect(
        "ca/issued/device-test-002.pem", "ca/issued/device-test-002-key.pem",
        "device-test-002",
    ),
    "revoked then unrevoked device-revoked-001": f"{code_revoked} -> {code_unrevoked}",
    "spoofed creds on device-test-001 cert": connect(
        "ca/issued/device-test-001.pem", "ca/issued/device-test-001-key.pem",
        "device-test-002", "device-test-002", "device-test-002",
    ),
}

for label, code in codes.items():
    print(f"CONNACK ({label}): {code}")

ok = codes["cert-only device-test-001"] == 0
ok = ok and codes["cert-only device-test-002"] == 0
ok = ok and code_revoked != 0 and code_unrevoked == 0
ok = ok and codes["spoofed creds on device-test-001 cert"] != 0
sys.exit(0 if ok else 1)
