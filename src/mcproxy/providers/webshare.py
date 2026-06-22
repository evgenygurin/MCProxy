"""Webshare adapter.

Docs: https://apidocs.webshare.io/
Base URL: https://proxy.webshare.io/api/v2/
Auth: ``Authorization: Token <API_KEY>``
"""

from __future__ import annotations

from ..http import json_or_raise
from ..models import (
    BalanceInfo,
    CountryListResult,
    Operation,
    ProxyEndpoint,
    ProxyListResult,
    ProxyProtocol,
    ProxyType,
    UsageInfo,
)
from .base import BaseProvider

BASE_URL = "https://proxy.webshare.io/api/v2"


class WebshareProvider(BaseProvider):
    name = "webshare"
    display_name = "Webshare"
    website = "https://www.webshare.io"
    country_of_origin = "US"
    proxy_types = [ProxyType.DATACENTER, ProxyType.ISP, ProxyType.RESIDENTIAL]
    operations = [
        Operation.LIST_PROXIES,
        Operation.CHECK_BALANCE,
        Operation.GET_USAGE,
        Operation.LIST_COUNTRIES,
    ]
    credential_env = ["WEBSHARE_API_KEY", "WEBSHARE_TOKEN"]
    notes = "Developer-friendly, has a free tier. Token auth, clean REST API."

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Token {self.require_credential()}"}

    async def list_proxies(
        self,
        proxy_type: ProxyType | None = None,
        country: str | None = None,
        limit: int = 100,
    ) -> ProxyListResult:
        params: dict[str, str | int] = {"mode": "direct", "page": 1, "page_size": min(limit, 100)}
        if country:
            params["country_code__in"] = country.upper()
        async with self.client(base_url=BASE_URL, headers=self._headers()) as client:
            data = json_or_raise(await client.get("/proxy/list/", params=params))

        proxies: list[ProxyEndpoint] = []
        for item in data.get("results", [])[:limit]:
            proxies.append(
                ProxyEndpoint(
                    host=item.get("proxy_address"),
                    port=item.get("port"),
                    username=item.get("username"),
                    password=item.get("password"),
                    protocol=ProxyProtocol.HTTP,
                    country=item.get("country_code"),
                    label=item.get("city_name"),
                )
            )
        return ProxyListResult.from_endpoints(
            self.name, proxies, note=f"{data.get('count', len(proxies))} total proxies on account."
        )

    async def check_balance(self) -> BalanceInfo:
        async with self.client(base_url=BASE_URL, headers=self._headers()) as client:
            data = json_or_raise(await client.get("/subscription/"))
        # Webshare is subscription-based; surface remaining bandwidth where present.
        sub = data.get("results", [data])[0] if isinstance(data, dict) else {}
        remaining = sub.get("bandwidth_limit")
        gb = round(remaining / 1_000_000_000, 2) if isinstance(remaining, (int, float)) else None
        return BalanceInfo(provider=self.name, traffic_remaining_gb=gb, raw=data)

    async def get_usage(self) -> UsageInfo:
        async with self.client(base_url=BASE_URL, headers=self._headers()) as client:
            data = json_or_raise(await client.get("/subscription/"))
        return UsageInfo(provider=self.name, raw=data)

    async def list_countries(self, proxy_type: ProxyType | None = None) -> CountryListResult:
        # Derive available countries from the account's proxy list.
        async with self.client(base_url=BASE_URL, headers=self._headers()) as client:
            data = json_or_raise(
                await client.get("/proxy/list/", params={"mode": "direct", "page_size": 100})
            )
        codes: dict[str, int] = {}
        for item in data.get("results", []):
            code = item.get("country_code")
            if code:
                codes[code] = codes.get(code, 0) + 1
        countries = [self._country(code=c, count=n) for c, n in sorted(codes.items())]
        return CountryListResult(provider=self.name, count=len(countries), countries=countries)
