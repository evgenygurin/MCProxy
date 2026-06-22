"""Shared async HTTP helpers for provider adapters."""

from __future__ import annotations

from typing import Any

import httpx

from .config import get_settings


def build_client(
    base_url: str = "",
    headers: dict[str, str] | None = None,
    auth: httpx.Auth | tuple[str, str] | None = None,
    timeout: float | None = None,
) -> httpx.AsyncClient:
    """Create an ``httpx.AsyncClient`` pre-configured from global settings."""

    settings = get_settings()
    return httpx.AsyncClient(
        base_url=base_url,
        headers=headers or {},
        auth=auth,
        timeout=timeout or settings.request_timeout,
        follow_redirects=True,
    )


def raise_for_status(response: httpx.Response) -> None:
    """Raise a readable error including the response body on HTTP failures."""

    if response.is_success:
        return
    body = response.text
    if len(body) > 500:
        body = body[:500] + "…"
    raise httpx.HTTPStatusError(
        f"{response.request.method} {response.request.url} -> "
        f"{response.status_code} {response.reason_phrase}: {body}",
        request=response.request,
        response=response,
    )


def json_or_raise(response: httpx.Response) -> Any:
    raise_for_status(response)
    return response.json()
