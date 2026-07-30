"""
Hardcoded device registry and permission rules.

Each device is identified by its certificate Common Name (CN).
The CN must match an entry in DEVICES dict.

Format:
    DEVICES = {
        "<CN>": {
            "description": "...",
            "topics": {
                "write": ["topic/pattern/#"],
                "read":  ["topic/pattern/#"],
            },
        },
    }
"""

DEVICES: dict[str, dict] = {
    "device-test-001": {
        "description": "Development test device",
        "topics": {
            "write": ["devices/device-test-001/telemetry/#"],
            "read":  ["devices/device-test-001/commands/#"],
        },
    },
    "device-test-002": {
        "description": "Second development test device",
        "topics": {
            "write": ["devices/device-test-002/telemetry/#"],
            "read":  ["devices/device-test-002/commands/#"],
        },
    },
    "central": {
        "description": "Central process consuming all telemetry",
        "topics": {
            "read": ["devices/#"],
        },
    },
}


def authenticate_device(username: str) -> bool:
    return username in DEVICES


def check_vhost_access(username: str, vhost: str) -> bool:
    return vhost == "/"


def check_resource_access(
    username: str, vhost: str, resource: str, name: str, permission: str
) -> bool:
    return vhost == "/"


def _match_topic(pattern: str, routing_key: str) -> bool:
    p_parts = pattern.split("/")
    r_parts = routing_key.split("/")

    if r_parts[0].startswith("$") and p_parts[0] in ("+", "#"):
        return False

    pi = 0
    ri = 0
    while pi < len(p_parts) and ri < len(r_parts):
        p = p_parts[pi]
        if p == "#":
            return True
        if p == "+":
            pi += 1
            ri += 1
            continue
        if p != r_parts[ri]:
            return False
        pi += 1
        ri += 1

    if pi == len(p_parts) and ri == len(r_parts):
        return True
    if pi < len(p_parts) and p_parts[pi] == "#":
        return True
    return False


def check_topic_access(
    username: str, vhost: str, resource: str, name: str,
    permission: str, routing_key: str,
) -> bool:
    device = DEVICES.get(username)
    if device is None:
        return False

    # RabbitMQ converts MQTT / to AMQP . in routing keys
    routing_key = routing_key.replace(".", "/")

    allowed_topics = device["topics"].get(permission, [])
    return any(_match_topic(pattern, routing_key) for pattern in allowed_topics)
