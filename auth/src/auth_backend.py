"""
Authentication and authorization rules for AeroRadio2.

MQTT devices authenticate exclusively by their TLS client certificate.
RabbitMQ (mqtt.ssl_cert_login=true) derives the username from the certificate
Common Name (CN) and calls /auth/user without a password field (the MQTT
plugin drops the password when it is the "none" sentinel). There is therefore
no registry of valid MQTT devices: any certificate signed by the project CA
authenticates, unless its CN is on the revocation list.

The revocation list is a simple in-memory set. External processes feed it
through POST /auth/revoke and POST /auth/unrevoke on port 8000. It is lost on
restart of the auth backend.

AMQP service clients (e.g. `central`) authenticate with username/password
against SERVICE_ACCOUNTS. The two protocols are told apart by the presence of
a `client_id`: MQTT always provides one, AMQP never does.

MQTT connections that carry a username/password are rejected: RabbitMQ would
otherwise let the CONNECT credentials take priority over the certificate CN,
which would allow any certificate holder to impersonate another device.
"""

import re

# Certificate CN sanity rule. Any certificate CN that does not match is
# refused. This is a format rule, not a device registry.
CN_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")

# In-memory revocation list, fed by external processes via /auth/revoke and
# /auth/unrevoke. Empty at startup.
revoked_cns: set[str] = set()

# AMQP service accounts: username -> password. These are the only clients that
# use login/password (RabbitMQ 5672). They are NOT MQTT devices.
SERVICE_ACCOUNTS: dict[str, str] = {
    "central": "central",
}


def is_revoked(cn: str) -> bool:
    return cn in revoked_cns


def valid_cn(cn: str) -> bool:
    return bool(CN_PATTERN.match(cn or ""))


def authenticate_user(username: str, password: str = "", client_id: str = "") -> bool:
    if client_id:
        # MQTT: the certificate is the only credential. A supplied password
        # means the CONNECT packet carried credentials, which would bypass the
        # certificate identity in RabbitMQ — refuse.
        if password:
            return False
        if not valid_cn(username):
            return False
        if is_revoked(username):
            return False
        return True

    # AMQP service account.
    return SERVICE_ACCOUNTS.get(username) == password


def check_vhost_access(username: str, vhost: str) -> bool:
    return vhost == "/"


def check_resource_access(
    username: str, vhost: str, resource: str, name: str, permission: str
) -> bool:
    return vhost == "/"


def check_topic_access(
    username: str, vhost: str, resource: str, name: str,
    permission: str, routing_key: str,
) -> bool:
    # Policy decision: any certificate-authenticated device may use any topic.
    return True
