"""Configuration and credential loading.

Credentials are read from environment variables (optionally via a local ``.env``
file). Each provider adapter declares the variable names it needs; this module
provides typed access to global settings plus a small helper for reading the
per-provider secrets.
"""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global server settings (env-prefixed with ``MCPROXY_``)."""

    model_config = SettingsConfigDict(
        env_prefix="MCPROXY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Transport
    transport: str = "stdio"  # stdio | http | sse
    host: str = "127.0.0.1"
    port: int = 8000

    # HTTP client behaviour for outbound provider calls
    request_timeout: float = 30.0
    max_retries: int = 2

    # Optional default provider used by provider-agnostic convenience tools
    default_provider: str | None = None

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_credential(*names: str) -> str | None:
    """Return the first non-empty environment variable among ``names``.

    Adapters accept multiple aliases (e.g. a token may be configured under
    ``WEBSHARE_API_KEY`` or ``WEBSHARE_TOKEN``); the first that is set wins.
    """

    for name in names:
        value = os.environ.get(name)
        if value:
            return value.strip()
    return None


def has_credentials(*names: str) -> bool:
    return get_credential(*names) is not None
