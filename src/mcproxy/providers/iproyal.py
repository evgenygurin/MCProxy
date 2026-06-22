"""IPRoyal adapter (residential API).

Docs: https://docs.iproyal.com/proxies/residential/api
Base URL: https://resi-api.iproyal.com/v1
Auth: ``Authorization: Bearer <API_TOKEN>``

Residential traffic never expires; ``available_traffic`` is reported in GB.
The datacenter/ISP reseller API lives on a different host and auth scheme
(``X-Access-Token`` against https://apid.iproyal.com/v1/reseller) and is not
wired up here yet.
"""

from __future__ import annotations

from ..http import json_or_raise
from ..models import (
    BalanceInfo,
    CountryListResult,
    GeoTarget,
    Operation,
    ProxyEndpoint,
    ProxyListResult,
    ProxyProtocol,
    ProxyType,
    Rotation,
    UsageInfo,
)
from .base import BaseProvider, OperationNotSupported

BASE_URL = "https://resi-api.iproyal.com/v1"
DEFAULT_HOST = "geo.iproyal.com"


class IPRoyalProvider(BaseProvider):
    name = "iproyal"
    display_name = "IPRoyal"
    website = "https://iproyal.com"
    country_of_origin = "LT"
    proxy_types = [ProxyType.RESIDENTIAL]
    operations = [
        Operation.GENERATE_PROXY_LIST,
        Operation.CHECK_BALANCE,
        Operation.GET_USAGE,
        Operation.LIST_COUNTRIES,
    ]
    credential_env = ["IPROYAL_API_TOKEN", "IPROYAL_TOKEN"]
    notes = "Residential traffic never expires. Sticky sessions via lifetime (e.g. '2h')."

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.require_credential()}"}

    @staticmethod
    def _location(geo: GeoTarget) -> str:
        parts: list[str] = []
        if geo.country:
            parts.append(f"_country-{geo.country.lower()}")
        if geo.region:
            parts.append(f"_state-{geo.region.lower().replace(' ', '')}")
        if geo.city:
            parts.append(f"_city-{geo.city.lower().replace(' ', '')}")
        if geo.isp:
            parts.append(f"_isp-{geo.isp.lower().replace(' ', '')}")
        return "".join(parts)

    async def generate_proxy_list(
        self,
        proxy_type: ProxyType,
        geo: GeoTarget,
        count: int = 1,
        rotation: Rotation = Rotation.ROTATING,
        session_duration: str | None = None,
        protocol: ProxyProtocol = ProxyProtocol.HTTP,
    ) -> ProxyListResult:
        if proxy_type not in (ProxyType.RESIDENTIAL,):
            raise OperationNotSupported(
                "IPRoyal adapter currently generates residential proxies only."
            )
        port_kind = "socks5" if protocol is ProxyProtocol.SOCKS5 else "http|https"
        body = {
            "format": "{hostname}:{port}:{username}:{password}",
            "hostname": DEFAULT_HOST,
            "port": port_kind,
            "rotation": "sticky" if rotation is Rotation.STICKY else "random",
            "location": self._location(geo),
            "proxy_count": count,
        }
        if rotation is Rotation.STICKY and session_duration:
            body["lifetime"] = session_duration

        async with self.client(base_url=BASE_URL, headers=self._headers()) as client:
            lines = json_or_raise(
                await client.post("/access/generate-proxy-list", json=body)
            )

        proxies: list[ProxyEndpoint] = []
        out_protocol = ProxyProtocol.SOCKS5 if protocol is ProxyProtocol.SOCKS5 else ProxyProtocol.HTTP
        for line in lines:
            parts = str(line).split(":")
            if len(parts) < 4:
                continue
            host, port, username = parts[0], parts[1], parts[2]
            password = ":".join(parts[3:])
            try:
                port_int = int(port)
            except ValueError:
                port_int = 12321  # IPRoyal default residential port when placeholder returned
            proxies.append(
                ProxyEndpoint(
                    host=host,
                    port=port_int,
                    username=username,
                    password=password,
                    protocol=out_protocol,
                    proxy_type=ProxyType.RESIDENTIAL,
                    country=geo.country,
                    rotation=rotation,
                )
            )
        return ProxyListResult.from_endpoints(self.name, proxies)

    async def check_balance(self) -> BalanceInfo:
        async with self.client(base_url=BASE_URL, headers=self._headers()) as client:
            data = json_or_raise(await client.get("/residential/me"))
        return BalanceInfo(
            provider=self.name,
            traffic_remaining_gb=data.get("available_traffic"),
            raw=data,
        )

    async def get_usage(self) -> UsageInfo:
        async with self.client(base_url=BASE_URL, headers=self._headers()) as client:
            data = json_or_raise(await client.get("/residential/me"))
        return UsageInfo(
            provider=self.name,
            traffic_total_gb=data.get("available_traffic"),
            raw=data,
        )

    async def list_countries(self, proxy_type: ProxyType | None = None) -> CountryListResult:
        async with self.client(base_url=BASE_URL, headers=self._headers()) as client:
            data = json_or_raise(await client.get("/access/countries"))
        countries = [
            self._country(code=c.get("code"), name=c.get("name"))
            for c in data.get("countries", [])
        ]
        return CountryListResult(provider=self.name, count=len(countries), countries=countries)
