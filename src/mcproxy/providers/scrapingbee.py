"""ScrapingBee adapter.

Docs: https://www.scrapingbee.com/documentation/
Endpoint: https://app.scrapingbee.com/api/v1/ (GET with api_key + url)
Usage:    https://app.scrapingbee.com/api/v1/usage
Auth: API key as query parameter (also accepts Bearer).
"""

from __future__ import annotations

from ..http import as_float, json_or_raise, raise_for_status
from ..models import Operation, ProxyType, ScrapeResult, UsageInfo
from .base import BaseProvider

BASE_URL = "https://app.scrapingbee.com/api/v1"


class ScrapingBeeProvider(BaseProvider):
    name = "scrapingbee"
    display_name = "ScrapingBee"
    website = "https://www.scrapingbee.com"
    country_of_origin = "FR"
    proxy_types = [ProxyType.SCRAPING_API]
    operations = [Operation.SCRAPE, Operation.GET_USAGE]
    credential_env = ["SCRAPINGBEE_API_KEY", "SCRAPINGBEE_KEY"]
    notes = "Scraping API with JS rendering, premium/stealth proxies and extraction rules."

    async def scrape(
        self,
        url: str,
        render_js: bool = False,
        country: str | None = None,
        premium: bool = False,
    ) -> ScrapeResult:
        params: dict[str, str] = {
            "api_key": self.require_credential(),
            "url": url,
            "render_js": "true" if render_js else "false",
        }
        if country:
            params["country_code"] = country.lower()
        if premium:
            params["premium_proxy"] = "true"
        async with self.client(base_url=BASE_URL) as client:
            resp = await client.get("/", params=params)
            raise_for_status(resp)
        return ScrapeResult(
            provider=self.name,
            url=url,
            status_code=resp.status_code,
            content=resp.text,
            cost=as_float(resp.headers.get("Spb-cost")),
        )

    async def get_usage(self) -> UsageInfo:
        async with self.client(base_url=BASE_URL) as client:
            data = json_or_raise(
                await client.get("/usage", params={"api_key": self.require_credential()})
            )
        return UsageInfo(
            provider=self.name,
            requests_used=data.get("used_api_credit"),
            raw=data,
        )
