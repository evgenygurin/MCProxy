"""Catalog of documented providers that don't yet have a full adapter.

These are surfaced by ``list_providers`` so an agent can see the whole landscape
(and which env vars a future adapter would need), even though the operations
aren't wired up yet. Each upstream has a public REST API per our research; the
adapter is simply planned, not impossible.
"""

from __future__ import annotations

from ..models import ProviderCapabilities, ProxyType

_PLANNED = "API documented; adapter planned (contributions welcome)."


def planned_catalog() -> list[ProviderCapabilities]:
    def cap(
        name: str,
        display: str,
        website: str,
        origin: str,
        types: list[ProxyType],
        creds: list[str],
        notes: str,
    ) -> ProviderCapabilities:
        return ProviderCapabilities(
            name=name,
            display_name=display,
            country_of_origin=origin,
            website=website,
            proxy_types=types,
            operations=[],
            requires_credentials=creds,
            configured=False,
            notes=f"{notes} {_PLANNED}",
        )

    res, dc, mob, isp, scr = (
        ProxyType.RESIDENTIAL,
        ProxyType.DATACENTER,
        ProxyType.MOBILE,
        ProxyType.ISP,
        ProxyType.SCRAPING_API,
    )

    return [
        # Global enterprise / mid-tier
        cap("brightdata", "Bright Data", "https://brightdata.com", "IL", [res, dc, mob, isp],
            ["BRIGHTDATA_API_TOKEN"], "Market leader; deepest account/billing API (Bearer)."),
        cap("oxylabs", "Oxylabs", "https://oxylabs.io", "LT", [res, dc, mob, isp],
            ["OXYLABS_USERNAME", "OXYLABS_PASSWORD"], "Co-leader; Basic->JWT sub-user/stats API."),
        cap("decodo", "Decodo (Smartproxy)", "https://decodo.com", "CY", [res, dc, mob, isp],
            ["DECODO_API_KEY"], "Clean public API: endpoints, sub-users, whitelists."),
        cap("soax", "SOAX", "https://soax.com", "GB", [res, mob, isp, dc],
            ["SOAX_API_KEY"], "Unified credit model; package/IP/whitelist API."),
        cap("netnut", "NetNut", "https://netnut.io", "IL", [res, mob, isp],
            ["NETNUT_USERNAME", "NETNUT_PASSWORD"], "ISP-partnership network; Customers API (24h token)."),
        cap("infatica", "Infatica", "https://infatica.io", "SG", [res, dc, mob, isp],
            ["INFATICA_EMAIL", "INFATICA_PASSWORD"], "Client API for traffic/balance/locations."),
        cap("proxycheap", "Proxy-Cheap", "https://proxy-cheap.com", "EE", [res, dc, mob, isp],
            ["PROXYCHEAP_API_KEY", "PROXYCHEAP_API_SECRET"], "Full proxy lifecycle + programmatic ordering."),
        cap("zyte", "Zyte", "https://zyte.com", "IE", [scr],
            ["ZYTE_API_KEY"], "Zyte API scraping/unblocking (Basic auth)."),
        cap("nimble", "Nimble", "https://nimbleway.com", "IL", [res, scr],
            ["NIMBLE_USERNAME", "NIMBLE_PASSWORD"], "Premium residential + AI Web API."),
        cap("rayobyte", "Rayobyte", "https://rayobyte.com", "US", [res, dc, mob, isp],
            ["RAYOBYTE_API_KEY"], "Reseller API (docs gated; contact required)."),
        # RU / CIS
        cap("mobileproxy_space", "Mobile Proxy Space", "https://mobileproxy.space", "RU", [mob],
            ["MOBILEPROXY_SPACE_TOKEN"], "RU mobile 3G/4G/5G; command API + rotate link (Bearer)."),
        cap("iproxy_online", "iProxy.online", "https://iproxy.online", "RU", [mob],
            ["IPROXY_ONLINE_TOKEN"], "Richest mobile DIY API: rotation, SMS, ACLs (Bearer)."),
        cap("proxymarket", "ProxyMarket", "https://proxy.market", "RU", [res, dc, mob, isp],
            ["PROXYMARKET_API_TOKEN"], "Multi-type; Swagger API (purchase/renew/list)."),
        cap("froxy", "Froxy", "https://froxy.com", "EE", [res, mob, dc],
            ["FROXY_USERNAME", "FROXY_PASSWORD"], "Residential gateway + dashboard API."),
    ]
