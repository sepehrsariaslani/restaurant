from fastapi import Header, HTTPException, Request

from .config import load_settings


def verify_access(request: Request, x_local_api_key: str = Header(default="")):
    settings = load_settings()
    host = request.client.host if request.client else ""
    if settings.allowed_hosts and host not in settings.allowed_hosts:
        raise HTTPException(status_code=403, detail="Host is not allowed")

    if settings.api_key and x_local_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
