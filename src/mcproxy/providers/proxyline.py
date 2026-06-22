"""ProxyLine adapter (proxyline.net).

Docs: https://proxyline.net/api
Base URL: https://panel.proxyline.net/api/
Auth: ``API-KEY`` header (or ``api_key`` query param).
Rate limit: 50 req/min. IPv4/IPv6 datacenter only.
"""

from __future__ import annotations

from typing import Any

from ..http import as_float, json_or_raise, raise_for_status
from ..models import (
    BalanceInfo,
    CountryListResult,
    Operation,
    ProxyEndpoint,
    ProxyListResult,
    ProxyProtocol,
    ProxyType,
)
from .base import BaseProvider

BASE_URL = "https://panel.proxyline.net/api"


class ProxyLineProvider(BaseProvider):
    name = "proxyline"
    display_name = "ProxyLine"
    website = "https://proxyline.net"
    country_of_origin = "RU"
    proxy_types = [ProxyType.DATACENTER]
    operations = [
        Operation.LIST_PROXIES,
        Operation.CHECK_BALANCE,
        Operation.LIST_COUNTRIES,
        Operation.BUY_PROXIES,
        Operation.EXTEND_PROXIES,
        Operation.LIST_ORDERS,
    ]
    credential_env = ["PROXYLINE_API_KEY"]
    notes = "Cheap IPv4/IPv6 datacenter proxies; city-level selection."

    def _headers(self) -> dict[str, str]:
        return {"API-KEY": self.require_credential()}

    @staticmethod
    def _parse_line(line: str, protocol: ProxyProtocol) -> ProxyEndpoint | None:
        line = line.strip()
        if not line:
            return None
        user: str | None
        pw: str | None
        if "@" in line:  # user:pass@host:port
            creds, _, hostport = line.partition("@")
            user, _, pw = creds.partition(":")
            host, _, port = hostport.partition(":")
        else:  # host:port:user:pass
            parts = line.split(":")
            if len(parts) < 2:
                return None
            host, port = parts[0], parts[1]
            user = parts[2] if len(parts) > 2 else None
            pw = parts[3] if len(parts) > 3 else None
        return ProxyEndpoint(
            host=host,
            port=int(port) if port.isdigit() else 0,
            username=user or None,
            password=pw or None,
            protocol=protocol,
            proxy_type=ProxyType.DATACENTER,
        )

    async def list_proxies(
        self,
        proxy_type: ProxyType | None = None,
        country: str | None = None,
        limit: int = 100,
    ) -> ProxyListResult:
        protocol = ProxyProtocol.HTTP
        params: dict[str, Any] = {"format": "txt-http", "limit": min(limit, 2000)}
        if country:
            params["country"] = country.lower()
        async with self.client(base_url=BASE_URL, headers=self._headers()) as client:
            resp = await client.get("/proxies/", params=params)
            raise_for_status(resp)
            text = resp.text
        proxies: list[ProxyEndpoint] = []
        for line in text.splitlines():
            ep = self._parse_line(line, protocol)
            if ep:
                proxies.append(ep)
        return ProxyListResult.from_endpoints(self.name, proxies[:limit])

    async def check_balance(self) -> BalanceInfo:
        async with self.client(base_url=BASE_URL, headers=self._headers()) as client:
            data = json_or_raise(await client.get("/balance/"))
        return BalanceInfo(
            provider=self.name,
            balance=as_float(data.get("balance")),
            currency=data.get("currency"),
            raw=data,
        )

    async def list_countries(self, proxy_type: ProxyType | None = None) -> CountryListResult:
        async with self.client(base_url=BASE_URL, headers=self._headers()) as client:
            data = json_or_raise(await client.get("/countries/"))
        items = data if isinstance(data, list) else data.get("results", data.get("countries", []))
        countries = [
            self._country(code=c.get("code") or c.get("id"), name=c.get("name"))
            for c in items
            if isinstance(c, dict)
        ]
        return CountryListResult(provider=self.name, count=len(countries), countries=countries)

    async def buy_proxies(
        self,
        proxy_type: ProxyType,
        quantity: int,
        country: str | None = None,
        period_days: int | None = None,
        protocol: ProxyProtocol = ProxyProtocol.HTTP,
        extra: dict | None = None,
    ) -> ProxyListResult:
        body: dict[str, Any] = {
            "type": (extra or {}).get("type", "shared"),
            "ip_version": (extra or {}).get("ip_version", 4),
            "country": (country or "us").lower(),
            "quantity": quantity,
            "period": period_days or 30,
        }
        async with self.client(base_url=BASE_URL, headers=self._headers()) as client:
            data = json_or_raise(await client.post("/new-order/", json=body))
        return ProxyListResult.from_endpoints(
            self.name, [], note=f"Order placed: {data}. Call get_proxies to retrieve them."
        )

    async def extend_proxies(self, proxy_ids: list[str], period_days: int) -> dict:
        body = {"proxies": [int(i) for i in proxy_ids], "period": period_days}
        async with self.client(base_url=BASE_URL, headers=self._headers()) as client:
            data = json_or_raise(await client.post("/renew/", json=body))
        return {"provider": self.name, "extended": proxy_ids, "raw": data}
