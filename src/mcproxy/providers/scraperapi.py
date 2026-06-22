"""ScraperAPI adapter.

Docs: https://docs.scraperapi.com/
Endpoint: https://api.scraperapi.com/ (GET with api_key + url)
Account:  https://api.scraperapi.com/account?api_key=...
Auth: API key as query parameter.
"""

from __future__ import annotations

from ..http import as_float, json_or_raise, raise_for_status
from ..models import Operation, ProxyType, ScrapeResult, UsageInfo
from .base import BaseProvider

BASE_URL = "https://api.scraperapi.com"


class ScraperAPIProvider(BaseProvider):
    name = "scraperapi"
    display_name = "ScraperAPI"
    website = "https://www.scraperapi.com"
    country_of_origin = "US"
    proxy_types = [ProxyType.SCRAPING_API]
    operations = [Operation.SCRAPE, Operation.GET_USAGE]
    credential_env = ["SCRAPERAPI_API_KEY", "SCRAPERAPI_KEY"]
    notes = "Managed scraping API with auto rotation, JS rendering and unblocking."

    async def scrape(
        self,
        url: str,
        render_js: bool = False,
        country: str | None = None,
        premium: bool = False,
    ) -> ScrapeResult:
        params: dict[str, str] = {"api_key": self.require_credential(), "url": url}
        if render_js:
            params["render"] = "true"
        if country:
            params["country_code"] = country.lower()
        if premium:
            params["premium"] = "true"
        async with self.client(base_url=BASE_URL) as client:
            resp = await client.get("/", params=params)
            raise_for_status(resp)
        return ScrapeResult(
            provider=self.name,
            url=url,
            status_code=resp.status_code,
            content=resp.text,
            cost=as_float(resp.headers.get("sa-credit-cost")),
        )

    async def get_usage(self) -> UsageInfo:
        async with self.client(base_url=BASE_URL) as client:
            data = json_or_raise(
                await client.get("/account", params={"api_key": self.require_credential()})
            )
        return UsageInfo(
            provider=self.name,
            requests_used=data.get("requestCount"),
            raw=data,
        )
