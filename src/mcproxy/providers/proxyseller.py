"""Proxy-Seller adapter (proxy-seller.com / .ru, also powers Geonix).

Docs: https://docs.proxy-seller.com
Base URL: https://proxy-seller.com/personal/api/v1/{api_key}/  (API key in URL path)
Convention: business errors return HTTP 200 with a non-empty ``errors`` array.

Product ``type`` segment: ipv4, ipv6, isp, mobile, mix, mix_isp, resident.
Ordering uses a calc -> make two-step that is intentionally left out of this
adapter for now (it requires reference IDs); balance/list/countries are wired up.
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

API_HOST = "https://proxy-seller.com"

TYPE_MAP = {
    ProxyType.DATACENTER: "ipv4",
    ProxyType.ISP: "isp",
    ProxyType.MOBILE: "mobile",
    ProxyType.RESIDENTIAL: "resident",
}


class ProxySellerProvider(BaseProvider):
    name = "proxyseller"
    display_name = "Proxy-Seller"
    website = "https://proxy-seller.com"
    country_of_origin = "RU"
    proxy_types = [
        ProxyType.DATACENTER,
        ProxyType.ISP,
        ProxyType.MOBILE,
        ProxyType.RESIDENTIAL,
    ]
    operations = [
        Operation.LIST_PROXIES,
        Operation.CHECK_BALANCE,
        Operation.LIST_COUNTRIES,
    ]
    credential_env = ["PROXYSELLER_API_KEY"]
    notes = "Broadest RU product set (IPv4/IPv6/ISP/mobile/residential). USD."

    def _base(self) -> str:
        return f"{API_HOST}/personal/api/v1/{self.require_credential()}"

    @staticmethod
    def _unwrap(payload: dict[str, Any]) -> Any:
        errors = payload.get("errors")
        if errors:
            raise ProviderError(f"Proxy-Seller error: {errors}")
        return payload.get("data", payload)

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        async with self.client(base_url=self._base()) as client:
            return self._unwrap(json_or_raise(await client.get(path, params=params or {})))

    async def check_balance(self) -> BalanceInfo:
        data = await self._get("/balance/get")
        balance = data.get("summ") if isinstance(data, dict) else data
        return BalanceInfo(
            provider=self.name,
            balance=as_float(balance),
            currency=(data.get("currency") if isinstance(data, dict) else None) or "USD",
            raw=data if isinstance(data, dict) else {"balance": data},
        )

    async def list_proxies(
        self,
        proxy_type: ProxyType | None = None,
        country: str | None = None,
        limit: int = 100,
    ) -> ProxyListResult:
        seg = TYPE_MAP.get(proxy_type or ProxyType.DATACENTER, "ipv4")
        data = await self._get(f"/proxy/list/{seg}")
        items = data.get("items", data) if isinstance(data, dict) else data
        proxies: list[ProxyEndpoint] = []
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            is_socks = str(item.get("protocol", "")).lower() == "socks5"
            port = item.get("port_socks") if is_socks else item.get("port_http")
            proxies.append(
                ProxyEndpoint(
                    host=item.get("ip") or item.get("host"),
                    port=int(port) if port else 0,
                    username=item.get("login"),
                    password=item.get("password"),
                    protocol=ProxyProtocol.SOCKS5 if is_socks else ProxyProtocol.HTTP,
                    country=item.get("country"),
                    expires_at=item.get("date_end") or item.get("end_at"),
                )
            )
        if country:
            proxies = [p for p in proxies if (p.country or "").lower() == country.lower()]
        return ProxyListResult.from_endpoints(self.name, proxies[:limit])

    async def list_countries(self, proxy_type: ProxyType | None = None) -> CountryListResult:
        seg = TYPE_MAP.get(proxy_type or ProxyType.DATACENTER, "ipv4")
        data = await self._get(f"/reference/list/{seg}")
        raw: list[Any] = []
        if isinstance(data, dict):
            raw = data.get("country") or data.get("countries") or data.get("items") or []
        countries = [
            self._country(
                code=c.get("alpha3") or c.get("code") or str(c.get("id")),
                name=c.get("name"),
            )
            for c in raw
            if isinstance(c, dict)
        ]
        return CountryListResult(provider=self.name, count=len(countries), countries=countries)
