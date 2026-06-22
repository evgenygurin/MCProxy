"""The MCProxy FastMCP server.

Exposes a small, provider-agnostic tool surface. An agent that needs a proxy
calls one of these tools with a ``provider`` name; the server dispatches to the
matching adapter and returns a normalized result. Use ``list_providers`` first
to discover which providers are configured and what each one supports.
"""

from __future__ import annotations

from collections.abc import Awaitable
from typing import Annotated, Any

import httpx
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from .config import get_settings
from .models import (
    BalanceInfo,
    CountryListResult,
    GeoTarget,
    Operation,
    ProviderCapabilities,
    ProxyListResult,
    ProxyProtocol,
    ProxyType,
    Rotation,
    ScrapeResult,
    UsageInfo,
)
from .providers import (
    ProviderError,
    ProviderNotConfigured,
    get_registry,
)

READ_ONLY = {"readOnlyHint": True, "openWorldHint": True}
WRITE = {"readOnlyHint": False, "openWorldHint": True}

INSTRUCTIONS = """\
MCProxy gives you on-demand access to proxies from many providers (global and
Russian/CIS) through one interface.

Recommended flow:
1. Call `list_providers` to see which providers are configured and what
   operations each supports (list/generate/buy proxies, balance, countries).
2. Use `generate_proxy_list` (rotating/residential providers) or `get_proxies`
   (providers that sell fixed IPs) to obtain ready-to-use proxy strings. Each
   returned proxy includes a `url` field usable directly by an HTTP client.
3. Use `check_balance` / `get_usage` to monitor spend, `list_countries` to see
   targetable locations, and `buy_proxies` / `extend_proxies` where supported.
4. For managed scraping providers, use `scrape`.

Provider credentials are configured via environment variables on the server; you
never need to supply them. If a provider isn't configured, `list_providers`
shows `configured: false` and the env vars it needs.
"""


async def _dispatch[T](coro: Awaitable[T]) -> T:
    """Await a provider coroutine, translating failures into ToolError."""
    try:
        return await coro
    except ProviderNotConfigured as exc:
        raise ToolError(str(exc)) from exc
    except ProviderError as exc:
        raise ToolError(str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise ToolError(f"Upstream provider returned an error: {exc}") from exc
    except httpx.HTTPError as exc:
        raise ToolError(f"Could not reach the provider: {exc}") from exc


def build_server() -> FastMCP:
    mcp = FastMCP(
        "MCProxy",
        instructions=INSTRUCTIONS,
        version="0.1.0",
        website_url="https://github.com/evgenygurin/mcproxy",
    )
    registry = get_registry()

    @mcp.tool(
        annotations=READ_ONLY,
        tags={"discovery"},
    )
    def list_providers(
        configured_only: Annotated[
            bool, Field(description="Only return providers that have credentials configured.")
        ] = False,
    ) -> list[ProviderCapabilities]:
        """List all supported proxy providers and their capabilities.

        Always call this first. Shows each provider's proxy types, supported
        operations, whether it is configured, and the env vars it requires.
        """
        return registry.capabilities(configured_only=configured_only)

    @mcp.tool(annotations=READ_ONLY, tags={"discovery"})
    def get_provider_info(provider: str) -> ProviderCapabilities:
        """Get capabilities and configuration status for a single provider."""
        return registry.get(provider).capabilities()

    @mcp.tool(annotations=READ_ONLY, tags={"proxies"})
    async def get_proxies(
        provider: str,
        proxy_type: ProxyType | None = None,
        country: Annotated[
            str | None, Field(description="ISO 3166-1 alpha-2 country code, e.g. 'US'.")
        ] = None,
        limit: Annotated[int, Field(ge=1, le=1000)] = 20,
        ctx: Context | None = None,
    ) -> ProxyListResult:
        """List proxies already on your account with a given provider.

        Best for providers that sell fixed IPs (e.g. proxy6, proxyline, webshare,
        proxymesh). For rotating/residential pools, prefer `generate_proxy_list`.
        """
        if ctx:
            await ctx.info(f"Listing proxies from {provider}")
        return await _dispatch(
            registry.get(provider).list_proxies(proxy_type=proxy_type, country=country, limit=limit)
        )

    @mcp.tool(annotations=READ_ONLY, tags={"proxies"})
    async def generate_proxy_list(
        provider: str,
        proxy_type: ProxyType = ProxyType.RESIDENTIAL,
        country: Annotated[str | None, Field(description="ISO alpha-2 country code.")] = None,
        city: str | None = None,
        region: str | None = None,
        isp: str | None = None,
        count: Annotated[int, Field(ge=1, le=1000)] = 1,
        rotation: Rotation = Rotation.ROTATING,
        session_duration: Annotated[
            str | None,
            Field(description="For sticky sessions, e.g. '10m', '2h'. Ignored when rotating."),
        ] = None,
        protocol: ProxyProtocol = ProxyProtocol.HTTP,
    ) -> ProxyListResult:
        """Generate ready-to-use proxy strings with geo-targeting and rotation.

        Best for residential/rotating providers (e.g. iproyal). Each proxy in the
        result has a `url` field usable directly as an HTTP/SOCKS5 proxy.
        """
        geo = GeoTarget(country=country, city=city, region=region, isp=isp)
        return await _dispatch(
            registry.get(provider).generate_proxy_list(
                proxy_type=proxy_type,
                geo=geo,
                count=count,
                rotation=rotation,
                session_duration=session_duration,
                protocol=protocol,
            )
        )

    @mcp.tool(annotations=READ_ONLY, tags={"account"})
    async def check_balance(provider: str) -> BalanceInfo:
        """Check the account balance / remaining traffic allowance for a provider."""
        return await _dispatch(registry.get(provider).check_balance())

    @mcp.tool(annotations=READ_ONLY, tags={"account"})
    async def get_usage(provider: str) -> UsageInfo:
        """Get traffic / request usage statistics for a provider."""
        return await _dispatch(registry.get(provider).get_usage())

    @mcp.tool(annotations=READ_ONLY, tags={"discovery"})
    async def list_countries(
        provider: str, proxy_type: ProxyType | None = None
    ) -> CountryListResult:
        """List the countries/locations targetable with a provider."""
        return await _dispatch(registry.get(provider).list_countries(proxy_type=proxy_type))

    @mcp.tool(annotations=WRITE, tags={"proxies", "billing"})
    async def buy_proxies(
        provider: str,
        proxy_type: ProxyType,
        quantity: Annotated[int, Field(ge=1, le=10000)],
        country: str | None = None,
        period_days: Annotated[int, Field(ge=1, le=3650)] = 30,
        protocol: ProxyProtocol = ProxyProtocol.HTTP,
        ctx: Context | None = None,
    ) -> ProxyListResult:
        """Purchase new proxies. This spends real money on the provider account.

        Only available for providers that support programmatic ordering (e.g.
        proxy6, proxystore, proxyline). Check `list_providers` first.
        """
        if ctx:
            await ctx.warning(
                f"Purchasing {quantity} {proxy_type} proxies from {provider} for {period_days}d"
            )
        return await _dispatch(
            registry.get(provider).buy_proxies(
                proxy_type=proxy_type,
                quantity=quantity,
                country=country,
                period_days=period_days,
                protocol=protocol,
            )
        )

    @mcp.tool(annotations=WRITE, tags={"proxies", "billing"})
    async def extend_proxies(
        provider: str,
        proxy_ids: list[str],
        period_days: Annotated[int, Field(ge=1, le=3650)],
    ) -> dict[str, Any]:
        """Extend/renew existing proxies by their IDs. Spends real money."""
        return await _dispatch(
            registry.get(provider).extend_proxies(proxy_ids=proxy_ids, period_days=period_days)
        )

    @mcp.tool(annotations=READ_ONLY, tags={"scraping"})
    async def scrape(
        provider: str,
        url: str,
        render_js: bool = False,
        country: str | None = None,
        premium: Annotated[
            bool, Field(description="Use premium residential/mobile pool for hard targets.")
        ] = False,
    ) -> ScrapeResult:
        """Fetch a URL through a managed scraping API (e.g. scraperapi, scrapingbee)."""
        return await _dispatch(
            registry.get(provider).scrape(
                url=url, render_js=render_js, country=country, premium=premium
            )
        )

    @mcp.tool(annotations=READ_ONLY, tags={"proxies"})
    async def acquire_proxy(
        proxy_type: ProxyType = ProxyType.RESIDENTIAL,
        country: str | None = None,
        ctx: Context | None = None,
    ) -> ProxyListResult:
        """Get a single ready-to-use proxy from any configured provider.

        Convenience for "I just need a proxy now": picks the first configured
        provider that can serve the requested type, preferring generation over
        listing. Use the more specific tools for control over which provider.
        """
        settings = get_settings()
        candidates = registry.capabilities(configured_only=True)
        # Honor an explicit default provider if set and configured.
        if settings.default_provider:
            candidates.sort(key=lambda c: c.name != settings.default_provider)

        last_error: Exception | None = None
        for cap in candidates:
            if proxy_type not in cap.proxy_types:
                continue
            provider = registry.get(cap.name)
            try:
                if Operation.GENERATE_PROXY_LIST in cap.operations:
                    return await provider.generate_proxy_list(
                        proxy_type=proxy_type, geo=GeoTarget(country=country), count=1
                    )
                if Operation.LIST_PROXIES in cap.operations:
                    result = await provider.list_proxies(proxy_type=proxy_type, country=country, limit=1)
                    if result.proxies:
                        return result
            except (ProviderError, httpx.HTTPError) as exc:  # try the next provider
                last_error = exc
                if ctx:
                    await ctx.warning(f"{cap.name} failed: {exc}")
                continue
        raise ToolError(
            "No configured provider could supply a "
            f"{proxy_type} proxy"
            + (f" in {country}" if country else "")
            + (f" (last error: {last_error})" if last_error else "")
            + ". Configure a provider (see list_providers) or relax the request."
        )

    @mcp.custom_route("/health", methods=["GET"])
    async def health(_request: Any):  # pragma: no cover - trivial
        from starlette.responses import JSONResponse

        return JSONResponse({"status": "ok", "providers": registry.names()})

    return mcp


mcp = build_server()
