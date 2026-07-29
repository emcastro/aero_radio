from urllib.request import Request, urlopen
from urllib.parse import urlencode

BASE = "http://localhost:8000/auth"


def post(path: str, data: dict[str, str]) -> str:
    body = urlencode(data).encode()
    req = Request(f"{BASE}/{path}", data=body)
    return urlopen(req).read().decode().strip()


print("/auth/user:", post("user", {"username": "device-test-001", "password": ""}))
print("/auth/vhost:", post("vhost", {"username": "device-test-001", "vhost": "/"}))
print(
    "/auth/topic(write):",
    post(
        "topic",
        {
            "username": "device-test-001",
            "vhost": "/",
            "resource": "topic",
            "name": "amq.topic",
            "permission": "write",
            "routing_key": "devices.device-test-001.telemetry.temp",
        },
    ),
)
print(
    "/auth/topic(read):",
    post(
        "topic",
        {
            "username": "device-test-001",
            "vhost": "/",
            "resource": "topic",
            "name": "amq.topic",
            "permission": "read",
            "routing_key": "devices.device-test-001.commands.#",
        },
    ),
)
