import sys
from urllib.request import Request, urlopen
from urllib.parse import urlencode

BASE = "http://localhost:8000/auth"


def post(path: str, data: dict[str, str]) -> str:
    body = urlencode(data).encode()
    req = Request(f"{BASE}/{path}", data=body)
    return urlopen(req).read().decode().strip()


# MQTT (client_id present): certificate-only. RabbitMQ drops the password
# field entirely for cert-authenticated MQTT, so these requests mirror that by
# not sending it. A supplied password is a bypass attempt -> deny.
# AMQP (no client_id): service account login/password.
cases = {
    "/auth/user (mqtt cert-only)": post("user", {"username": "device-test-001", "client_id": "device-test-001"}),
    "/auth/user (mqtt cert-only other)": post("user", {"username": "device-test-002", "client_id": "device-test-002"}),
    "/auth/user (mqtt spoofed password)": post("user", {"username": "device-test-001", "password": "device-test-001", "client_id": "device-test-001"}),
    "/auth/user (mqtt invalid CN)": post("user", {"username": "bad/name", "client_id": "bad/name"}),
    "/auth/user (amqp service ok)": post("user", {"username": "central", "password": "central"}),
    "/auth/user (amqp wrong password)": post("user", {"username": "central", "password": "wrong"}),
    "/auth/user (amqp unknown user)": post("user", {"username": "ghost", "password": "x"}),
    "/auth/vhost": post("vhost", {"username": "device-test-001", "vhost": "/"}),
    "/auth/resource": post("resource", {"username": "central", "vhost": "/", "resource": "queue", "name": "q", "permission": "write"}),
    "/auth/topic": post("topic", {"username": "device-test-001", "vhost": "/", "resource": "topic", "name": "amq.topic", "permission": "write", "routing_key": "devices.device-test-002.secret.#"}),
}

# Revocation lifecycle (in-memory list fed via the revoke/unrevoke endpoints).
cases["/auth/revoke"] = post("revoke", {"cn": "device-revoked-001"})
cases["/auth/user (mqtt revoked after revoke)"] = post("user", {"username": "device-revoked-001", "client_id": "device-revoked-001"})
cases["/auth/unrevoke"] = post("unrevoke", {"cn": "device-revoked-001"})
cases["/auth/user (mqtt unrevoked)"] = post("user", {"username": "device-revoked-001", "client_id": "device-revoked-001"})

for label, value in cases.items():
    print(f"{label}: {value}")

expected = {
    "/auth/user (mqtt cert-only)": "allow",
    "/auth/user (mqtt cert-only other)": "allow",
    "/auth/user (mqtt spoofed password)": "deny",
    "/auth/user (mqtt invalid CN)": "deny",
    "/auth/user (amqp service ok)": "allow",
    "/auth/user (amqp wrong password)": "deny",
    "/auth/user (amqp unknown user)": "deny",
    "/auth/vhost": "allow",
    "/auth/resource": "allow",
    "/auth/topic": "allow",
    "/auth/revoke": "ok",
    "/auth/user (mqtt revoked after revoke)": "deny",
    "/auth/unrevoke": "ok",
    "/auth/user (mqtt unrevoked)": "allow",
}

sys.exit(0 if all(cases[k] == expected[k] for k in expected) else 1)
