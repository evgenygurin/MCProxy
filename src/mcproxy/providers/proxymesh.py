"""ProxyMesh adapter.

Docs: https://docs.proxymesh.com/article/8-api
Base URL: https://proxymesh.com
Auth: HTTP Basic (account username/password). Proxy access itself uses the same
Basic credentials or a whitelisted IP.
"""

from __future__ import annotations

from ..config import get_credential
from ..http import json_or_raise
from ..models import (
    CountryListResult,
    Operation,
    ProxyEndpoint,
    ProxyListResult,
    ProxyProtocol,
    ProxyType,
    UsageInfo,
)
from .base import BaseProvider, ProviderNotConfigured

BASE_URL = "https://proxymesh.com"


class ProxyMeshProvider(BaseProvider):
    name = "proxymesh"
    display_name = "ProxyMesh"
    website = "https://proxymesh.com"
    country_of_origin = "US"
    proxy_types = [ProxyType.DATACENTER, ProxyType.ISP]
    operations = [
        Operation.LIST_PROXIES,
        Operation.LIST_COUNTRIES,
        Operation.GET_USAGE,
    ]
    credential_env = ["PROXYMESH_USERNAME", "PROXYMESH_PASSWORD"]
    notes = "Rotating datacenter gateways. Auth via Basic creds or IP whitelist."

    def _auth(self) -> tuple[str, str]:
        user = get_credential("PROXYMESH_USERNAME")
        pw = get_credential("PROXYMESH_PASSWORD")
        if not user or not pw:
            raise ProviderNotConfigured(
                "ProxyMesh needs PROXYMESH_USERNAME and PROXYMESH_PASSWORD."
            )
        return user, pw

    def is_configured(self) -> bool:
        return bool(get_credential("PROXYMESH_USERNAME") and get_credential("PROXYMESH_PASSWORD"))

    async def list_proxies(
        self,
        proxy_type: ProxyType | None = None,
        country: str | None = None,
        limit: int = 100,
    ) -> ProxyListResult:
        user, pw = self._auth()
        async with self.client(base_url=BASE_URL, auth=(user, pw)) as client:
            data = json_or_raise(await client.get("/api/proxies/"))
        proxies: list[ProxyEndpoint] = []
        for entry in data.get("proxies", [])[:limit]:
            host, _, port = str(entry).partition(":")
            proxies.append(
                ProxyEndpoint(
                    host=host,
                    port=int(port) if port else 31280,
                    username=user,
                    password=pw,
                    protocol=ProxyProtocol.HTTP,
                    proxy_type=ProxyType.DATACENTER,
                )
            )
        return ProxyListResult.from_endpoints(
            self.name, proxies, note="Rotating gateways; each request exits a different IP."
        )

    async def list_countries(self, proxy_type: ProxyType | None = None) -> CountryListResult:
        user, pw = self._auth()
        async with self.client(base_url=BASE_URL, auth=(user, pw)) as client:
            data = json_or_raise(await client.get("/api/geoips/open/"))
        countries = [self._country(code=code, count=count) for code, count in data.items()]
        return CountryListResult(provider=self.name, count=len(countries), countries=countries)

    async def get_usage(self) -> UsageInfo:
        # ProxyMesh reports bandwidth per sub-account; surface the configured one.
        sub = get_credential("PROXYMESH_SUBACCOUNT")
        if not sub:
            raise ProviderNotConfigured(
                "Set PROXYMESH_SUBACCOUNT to the sub-account username to read its usage."
            )
        user, pw = self._auth()
        async with self.client(base_url=BASE_URL, auth=(user, pw)) as client:
            data = json_or_raise(
                await client.get("/api/sub/get/", params={"username": sub})
            )
        return UsageInfo(
            provider=self.name,
            traffic_used_gb=data.get("monthly_bandwidth"),
            traffic_total_gb=data.get("monthly_bandwidth_limit"),
            raw=data,
        )
