# ruff: noqa: B008
import logging
import secrets

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from src.config import config

logger = logging.getLogger("ip_sakti.api.auth")

api_key_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_token_scheme = HTTPBearer(auto_error=False)


def is_valid_api_key(provided_key: str, valid_keys: list[str]) -> bool:
    """Validate a provided API key against configured valid keys using constant-time comparison.

    Iterates through all configured keys to mitigate timing side-channel attacks.
    """
    if not provided_key or not valid_keys:
        return False

    is_valid = False
    for valid_key in valid_keys:
        if secrets.compare_digest(provided_key, valid_key):
            is_valid = True
    return is_valid


async def verify_api_key(
    request: Request,
    api_key_header: str | None = Security(api_key_header_scheme),
    bearer_auth: HTTPAuthorizationCredentials | None = Security(bearer_token_scheme),
) -> str:
    """FastAPI security dependency to verify API keys from X-API-Key or Authorization Bearer headers.

    Raises HTTP 401 if the key is missing or invalid.
    """
    key: str | None = None

    if api_key_header:
        key = api_key_header.strip()
    elif bearer_auth and bearer_auth.credentials:
        key = bearer_auth.credentials.strip()
    else:
        # Fallback inspection of raw headers
        raw_x_key = request.headers.get("x-api-key")
        if raw_x_key:
            key = raw_x_key.strip()
        else:
            raw_auth = request.headers.get("authorization")
            if raw_auth:
                parts = raw_auth.strip().split()
                if len(parts) == 2 and parts[0].lower() == "bearer":
                    key = parts[1].strip()

    if not key or not is_valid_api_key(key, config.API_KEYS):
        client_host = request.client.host if request.client else "unknown"
        logger.warning(
            "Unauthorized request to '%s' from %s: missing or invalid API key",
            request.url.path,
            client_host,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return key
