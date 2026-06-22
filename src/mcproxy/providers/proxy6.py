"""Proxy6 adapter (proxy6.net).

Docs: https://proxy6.net/developers
Base URL: https://px6.link/api/{api_key}/{method}/?{params}  (API key in URL path)
Auth: API key embedded in the path.
Balance is returned on *every* response (``balance`` + ``currency``).
Rate limit: 3 req/sec.

Version codes: 3 = shared IPv4, 4 = IPv4, 5 = MTProto, 6 = IPv6.
"""

from __future__ import annotations

from typing import Any

from ..http import json_or_raise
from ..models import (
    BalanceInfo,
    CountryListResult,
    Operation,
    ProxyEndpoint,
    ProxyListResult,
    ProxyProtocol,
    ProxyType,
)
from .base import BaseProvider, ProviderError

API_HOST = "https://px6.link"

# Map our generic request to Proxy6 "version" codes.
VERSION_IPV6 = 6
VERSION_IPV4 = 4
VERSION_IPV4_SHARED = 3


class Proxy6Provider(BaseProvider):
    name = "proxy6"
    display_name = "Proxy6"
    website = "https://proxy6.net"
    country_of_origin = "RU"
    proxy_types = [ProxyType.DATACENTER]
    operations = [
        Operation.LIST_PROXIES,
        Operation.CHECK_BALANCE,
        Operation.LIST_COUNTRIES,
        Operation.BUY_PROXIES,
        Operation.EXTEND_PROXIES,
    ]
    credential_env = ["PROXY6_API_KEY"]
    notes = "Budget IPv4/IPv6 datacenter specialist. Country-level geo only."

    def _base(self) -> str:
        return f"{API_HOST}/api/{self.require_credential()}"

    @staticmethod
    def _check(data: dict[str, Any]) -> dict[str, Any]:
        if data.get("status") == "no":
            raise ProviderError(
                f"Proxy6 error {data.get('error_id')}: {data.get('error')}"
            )
        return data

    async def _call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        async with self.client(base_url=self._base()) as client:
            return self._check(json_or_raise(await client.get(f"/{method}/", params=params or {})))

    @staticmethod
    def _protocol(value: str | None) -> ProxyProtocol:
        return ProxyProtocol.SOCKS5 if value == "socks" else ProxyProtocol.HTTP

    def _to_endpoints(self, listing: Any) -> list[ProxyEndpoint]:
        # Proxy6 returns "list" either as a dict keyed by id or a list.
        items = listing.values() if isinstance(listing, dict) else (listing or [])
        proxies: list[ProxyEndpoint] = []
        for item in items:
            proxies.append(
                ProxyEndpoint(
                    host=item.get("host") or item.get("ip"),
                    port=int(item["port"]),
                    username=item.get("user"),
                    password=item.get("pass"),
                    protocol=self._protocol(item.get("type")),
                    proxy_type=ProxyType.DATACENTER,
                    country=item.get("country"),
                    expires_at=item.get("date_end"),
                    label=item.get("descr") or None,
                )
            )
        return proxies

    async def check_balance(self) -> BalanceInfo:
        data = await self._call("getcountry", {"version": VERSION_IPV6})
        return BalanceInfo(
            provider=self.name,
            balance=float(data["balance"]) if "balance" in data else None,
            currency=data.get("currency"),
            raw={k: data[k] for k in ("balance", "currency", "user_id") if k in data},
        )

    async def list_countries(self, proxy_type: ProxyType | None = None) -> CountryListResult:
        data = await self._call("getcountry", {"version": VERSION_IPV6})
        codes = data.get("list", [])
        countries = [self._country(code=c) for c in codes]
        return CountryListResult(provider=self.name, count=len(countries), countries=countries)

    async def list_proxies(
        self,
        proxy_type: ProxyType | None = None,
        country: str | None = None,
        limit: int = 100,
    ) -> ProxyListResult:
        params: dict[str, Any] = {"state": "active", "limit": min(limit, 1000)}
        data = await self._call("getproxy", params)
        proxies = self._to_endpoints(data.get("list", {}))
        if country:
            proxies = [p for p in proxies if (p.country or "").lower() == country.lower()]
        return ProxyListResult.from_endpoints(self.name, proxies[:limit])

    async def buy_proxies(
        self,
        proxy_type: ProxyType,
        quantity: int,
        country: str | None = None,
        period_days: int | None = None,
        protocol: ProxyProtocol = ProxyProtocol.HTTP,
        extra: dict | None = None,
    ) -> ProxyListResult:
        version = (extra or {}).get("version", VERSION_IPV6)
        params: dict[str, Any] = {
            "count": quantity,
            "period": period_days or 30,
            "country": (country or "ru").lower(),
            "version": version,
            "type": "socks" if protocol is ProxyProtocol.SOCKS5 else "http",
        }
        if extra and extra.get("descr"):
            params["descr"] = extra["descr"]
        data = await self._call("buy", params)
        proxies = self._to_endpoints(data.get("list", {}))
        return ProxyListResult.from_endpoints(
            self.name, proxies, note=f"Purchased {quantity} proxies for {period_days or 30} days."
        )

    async def extend_proxies(self, proxy_ids: list[str], period_days: int) -> dict:
        data = await self._call(
            "prolong", {"period": period_days, "ids": ",".join(str(i) for i in proxy_ids)}
        )
        return {"provider": self.name, "extended": proxy_ids, "raw": data}
