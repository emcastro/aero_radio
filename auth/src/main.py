import logging
from typing import Annotated

from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse

from src.auth_backend import (
    authenticate_device,
    check_resource_access,
    check_topic_access,
    check_vhost_access,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="AeroRadio2 Auth Backend")


@app.post("/auth/user", response_class=PlainTextResponse)
async def auth_user(
    username: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
):
    ok = authenticate_device(username)
    if ok:
        return "allow administrator"
    return "deny"


@app.post("/auth/vhost", response_class=PlainTextResponse)
async def auth_vhost(
    username: Annotated[str, Form()] = "",
    vhost: Annotated[str, Form()] = "",
    ip: Annotated[str, Form()] = "",
):
    return "allow" if check_vhost_access(username, vhost) else "deny"


@app.post("/auth/resource", response_class=PlainTextResponse)
async def auth_resource(
    username: Annotated[str, Form()] = "",
    vhost: Annotated[str, Form()] = "",
    resource: Annotated[str, Form()] = "",
    name: Annotated[str, Form()] = "",
    permission: Annotated[str, Form()] = "",
):
    return "allow" if check_resource_access(username, vhost, resource, name, permission) else "deny"


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
