from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

from mcproxy.providers import get_registry


async def test_lists_expected_tools(client):
    async with client:
        tools = {t.name for t in await client.list_tools()}
    assert {
        "list_providers",
        "get_provider_info",
        "get_proxies",
        "generate_proxy_list",
        "check_balance",
        "buy_proxies",
        "scrape",
        "acquire_proxy",
    } <= tools


async def test_list_providers_returns_catalog(client):
    async with client:
        result = await client.call_tool("list_providers", {})
    names = {c.name for c in result.data}
    # implemented + planned providers both surface
    assert {"webshare", "iproyal", "proxy6", "proxyseller"} <= names
    assert {"brightdata", "oxylabs", "decodo"} <= names


async def test_configured_only_filters(client, monkeypatch):
    monkeypatch.delenv("WEBSHARE_API_KEY", raising=False)
    async with client:
        result = await client.call_tool("list_providers", {"configured_only": True})
    # nothing configured in a clean environment
    assert all(c.configured for c in result.data)


async def test_unknown_provider_raises(client):
    async with client:
        with pytest.raises(ToolError):
            await client.call_tool("check_balance", {"provider": "does-not-exist"})


async def test_unconfigured_provider_reports_clearly(client, monkeypatch):
    monkeypatch.delenv("PROXY6_API_KEY", raising=False)
    async with client:
        with pytest.raises(ToolError, match="not configured"):
            await client.call_tool("check_balance", {"provider": "proxy6"})


def test_registry_names_are_unique():
    names = get_registry().names()
    assert len(names) == len(set(names))
