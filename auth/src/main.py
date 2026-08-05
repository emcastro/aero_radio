import logging
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import PlainTextResponse

from auth_backend import (
    authenticate_user,
    check_resource_access,
    check_topic_access,
    check_vhost_access,
    revoked_cns,
)

logger = logging.getLogger("auth")

app = FastAPI(title="AeroRadio2 Auth Backend")

# https://github.com/rabbitmq/rabbitmq-server/tree/main/deps/rabbitmq_auth_backend_http#user_path
@app.post("/auth/user", response_class=PlainTextResponse)
async def auth_user(
    username: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
    client_id: Annotated[str, Form()] = "",
):
    ok = authenticate_user(username, password, client_id)
    if ok:
        return "allow"
    return "deny"

# https://github.com/rabbitmq/rabbitmq-server/tree/main/deps/rabbitmq_auth_backend_http#vhost_path
@app.post("/auth/vhost", response_class=PlainTextResponse)
async def auth_vhost(
    username: Annotated[str, Form()] = "",
    vhost: Annotated[str, Form()] = "",
    ip: Annotated[str, Form()] = "",
):
    return "allow" if check_vhost_access(username, vhost) else "deny"

# https://github.com/rabbitmq/rabbitmq-server/tree/main/deps/rabbitmq_auth_backend_http#resource_path
@app.post("/auth/resource", response_class=PlainTextResponse)
async def auth_resource(
    username: Annotated[str, Form()] = "",
    vhost: Annotated[str, Form()] = "",
    resource: Annotated[str, Form()] = "",
    name: Annotated[str, Form()] = "",
    permission: Annotated[str, Form()] = "",
):
    return "allow" if check_resource_access(username, vhost, resource, name, permission) else "deny"


# https://github.com/rabbitmq/rabbitmq-server/tree/main/deps/rabbitmq_auth_backend_http#topic_path
@app.post("/auth/topic", response_class=PlainTextResponse)
async def auth_topic(
    username: Annotated[str, Form()] = "",
    vhost: Annotated[str, Form()] = "",
    resource: Annotated[str, Form()] = "",
    name: Annotated[str, Form()] = "",
    permission: Annotated[str, Form()] = "",
    routing_key: Annotated[str, Form()] = "",
):
    logger.info("topic check: user=%s vhost=%s resource=%s name=%s perm=%s rk=%s", username, vhost, resource, name, permission, routing_key)
    ok = check_topic_access(username, vhost, resource, name, permission, routing_key)
    logger.info("topic check result: ok=%s", ok)
    return "allow" if ok else "deny"

# In-memory revocation list (dev port 8000, unauthenticated). External
# processes feed it at runtime: POST /auth/revoke to refuse a CN, POST
# /auth/unrevoke to allow it again. Reset on restart of the auth backend.
@app.post("/auth/revoke", response_class=PlainTextResponse)
async def auth_revoke(cn: Annotated[str, Form()] = ""):
    if not cn:
        raise HTTPException(status_code=400, detail="missing cn")
    revoked_cns.add(cn)
    return "ok"


@app.post("/auth/unrevoke", response_class=PlainTextResponse)
async def auth_unrevoke(cn: Annotated[str, Form()] = ""):
    if not cn:
        raise HTTPException(status_code=400, detail="missing cn")
    revoked_cns.discard(cn)
    return "ok"
