import logging
from typing import Annotated

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import PlainTextResponse

from src.config import settings
from src.auth_backend import (
    authenticate_device,
    check_resource_access,
    check_topic_access,
    check_vhost_access,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="AeroRadio2 Auth Backend")


def _verify_api_key(request: Request) -> None:
    api_key = request.query_params.get("api_key")
    if api_key != settings.auth_api_key:
        raise HTTPException(status_code=403, detail="invalid api_key")


@app.post("/auth/user", response_class=PlainTextResponse)
async def auth_user(
    request: Request,
    username: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
):
    _verify_api_key(request)
    ok = authenticate_device(username)
    if ok:
        return "allow administrator"
    return "deny"


@app.post("/auth/vhost", response_class=PlainTextResponse)
async def auth_vhost(
    request: Request,
    username: Annotated[str, Form()] = "",
    vhost: Annotated[str, Form()] = "",
    ip: Annotated[str, Form()] = "",
):
    _verify_api_key(request)
    return "allow" if check_vhost_access(username, vhost) else "deny"


@app.post("/auth/resource", response_class=PlainTextResponse)
async def auth_resource(
    request: Request,
    username: Annotated[str, Form()] = "",
    vhost: Annotated[str, Form()] = "",
    resource: Annotated[str, Form()] = "",
    name: Annotated[str, Form()] = "",
    permission: Annotated[str, Form()] = "",
):
    _verify_api_key(request)
    return "allow" if check_resource_access(username, vhost, resource, name, permission) else "deny"


@app.post("/auth/topic", response_class=PlainTextResponse)
async def auth_topic(
    request: Request,
    username: Annotated[str, Form()] = "",
    vhost: Annotated[str, Form()] = "",
    resource: Annotated[str, Form()] = "",
    name: Annotated[str, Form()] = "",
    permission: Annotated[str, Form()] = "",
    routing_key: Annotated[str, Form()] = "",
):
    _verify_api_key(request)
    logger.info("topic check: user=%s vhost=%s resource=%s name=%s perm=%s rk=%s", username, vhost, resource, name, permission, routing_key)
    ok = check_topic_access(username, vhost, resource, name, permission, routing_key)
    logger.info("topic check result: ok=%s", ok)
    return "allow" if ok else "deny"
