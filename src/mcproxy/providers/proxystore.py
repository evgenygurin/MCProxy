"""Proxy-Store adapter (proxy-store.com).

Docs: https://proxy-store.com/en/developers
Base URL: https://proxy-store.com/api/{api_key}/{method}/  (API key in URL path)
Same shape as Proxy6 but adds a dedicated ``getbalance`` method (returns USD).
"""

from __future__ import annotations

from typing import Any

from ..http import as_float, json_or_raise
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

API_HOST = "https://proxy-store.com"


class ProxyStoreProvider(BaseProvider):
    name = "proxystore"
    display_name = "Proxy-Store"
    website = "https://proxy-store.com"
    country_of_origin = "RU"
    proxy_types = [ProxyType.DATACENTER, ProxyType.RESIDENTIAL, ProxyType.MOBILE]
    operations = [
        Operation.LIST_PROXIES,
        Operation.CHECK_BALANCE,
        Operation.LIST_COUNTRIES,
        Operation.BUY_PROXIES,
        Operation.EXTEND_PROXIES,
    ]
    credential_env = ["PROXYSTORE_API_KEY"]
    notes = "Datacenter IPv4/IPv6, residential and mobile. USD balance."

    def _base(self) -> str:
        return f"{API_HOST}/api/{self.require_credential()}"

    @staticmethod
    def _check(data: dict[str, Any]) -> dict[str, Any]:
        status = data.get("status")
        if status in (False, "false", "no"):
            raise ProviderError(
                f"Proxy-Store error {data.get('error_id', '')}: {data.get('error', data)}"
            )
        return data

    async def _call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        async with self.client(base_url=self._base()) as client:
            return self._check(json_or_raise(await client.get(f"/{method}/", params=params or {})))

    def _to_endpoints(self, listing: Any) -> list[ProxyEndpoint]:
        items = listing.values() if isinstance(listing, dict) else (listing or [])
        proxies: list[ProxyEndpoint] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            proxies.append(
                ProxyEndpoint(
                    host=item.get("host") or item.get("ip"),
                    port=int(item["port"]) if item.get("port") else 0,
                    username=item.get("user"),
                    password=item.get("pass"),
                    protocol=ProxyProtocol.SOCKS5
                    if item.get("type") == "socks"
                    else ProxyProtocol.HTTP,
                    country=item.get("country"),
                    expires_at=item.get("date_end"),
                    label=item.get("descr") or None,
                )
            )
        return proxies

    async def check_balance(self) -> BalanceInfo:
        data = await self._call("getbalance")
        return BalanceInfo(
            provider=self.name,
            balance=as_float(data.get("balance")),
            currency=data.get("currency", "USD"),
            raw=data,
        )

    async def list_countries(self, proxy_type: ProxyType | None = None) -> CountryListResult:
        data = await self._call("getcountry")
        codes = data.get("list", data.get("countries", []))
        countries = [self._country(code=c) for c in codes] if isinstance(codes, list) else []
        return CountryListResult(provider=self.name, count=len(countries), countries=countries)

    async def list_proxies(
        self,
        proxy_type: ProxyType | None = None,
        country: str | None = None,
        limit: int = 100,
    ) -> ProxyListResult:
        data = await self._call("getproxy")
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
        params: dict[str, Any] = {
            "count": quantity,
            "period": period_days or 30,
            "country": (country or "us").lower(),
            "type": "socks" if protocol is ProxyProtocol.SOCKS5 else "http",
        }
        params.update(extra or {})
        data = await self._call("buy", params)
        return ProxyListResult.from_endpoints(
            self.name, self._to_endpoints(data.get("list", {})), note="Purchase completed."
        )

    async def extend_proxies(self, proxy_ids: list[str], period_days: int) -> dict:
        data = await self._call(
            "prolong", {"period": period_days, "ids": ",".join(str(i) for i in proxy_ids)}
        )
        return {"provider": self.name, "extended": proxy_ids, "raw": data}
