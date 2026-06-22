"""Shared, provider-agnostic data models.

Every provider adapter maps its native API responses onto these models so that
an AI agent gets a consistent shape no matter which proxy service it talks to.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ProxyType(StrEnum):
    """Category of proxy, normalized across providers."""

    RESIDENTIAL = "residential"
    DATACENTER = "datacenter"
    MOBILE = "mobile"
    ISP = "isp"  # static residential / ISP proxies
    SCRAPING_API = "scraping_api"  # managed scraping/unblocking endpoints


class ProxyProtocol(StrEnum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS5 = "socks5"


class Rotation(StrEnum):
    """How the exit IP behaves for a given proxy string."""

    ROTATING = "rotating"  # new IP per request (or per short interval)
    STICKY = "sticky"  # same IP held for the session lifetime


class Operation(StrEnum):
    """Capabilities a provider adapter may implement.

    Generic tools check a provider's declared operations before dispatching so
    the agent gets a clear "not supported" instead of an opaque error.
    """

    LIST_PROXIES = "list_proxies"
    GENERATE_PROXY_LIST = "generate_proxy_list"
    CHECK_BALANCE = "check_balance"
    GET_USAGE = "get_usage"
    LIST_COUNTRIES = "list_countries"
    BUY_PROXIES = "buy_proxies"
    EXTEND_PROXIES = "extend_proxies"
    LIST_ORDERS = "list_orders"
    SCRAPE = "scrape"


class GeoTarget(BaseModel):
    """Geographic / network targeting for a proxy request.

    Not every provider supports every field; adapters use what they can and
    ignore the rest.
    """

    country: str | None = Field(
        default=None,
        description="ISO 3166-1 alpha-2 country code, e.g. 'US', 'GB', 'RU'.",
    )
    region: str | None = Field(
        default=None, description="State / region / subdivision name or code."
    )
    city: str | None = Field(default=None, description="City name, e.g. 'new_york'.")
    asn: int | None = Field(default=None, description="Autonomous System Number to target.")
    isp: str | None = Field(default=None, description="ISP / carrier name or code.")
    zip_code: str | None = Field(default=None, description="Postal / ZIP code.")


class ProxyEndpoint(BaseModel):
    """A single ready-to-use proxy."""

    host: str
    port: int
    username: str | None = None
    password: str | None = None
    protocol: ProxyProtocol = ProxyProtocol.HTTP
    proxy_type: ProxyType | None = None
    country: str | None = None
    rotation: Rotation | None = None
    expires_at: str | None = Field(default=None, description="ISO 8601 expiry, if known.")
    label: str | None = None

    @property
    def url(self) -> str:
        """Connection string usable directly by HTTP clients."""
        auth = ""
        if self.username:
            auth = self.username
            if self.password:
                auth += f":{self.password}"
            auth += "@"
        return f"{self.protocol.value}://{auth}{self.host}:{self.port}"

    def as_dict(self) -> dict:
        data = self.model_dump(exclude_none=True)
        data["url"] = self.url
        return data


class ProxyListResult(BaseModel):
    """Result of listing or generating proxies."""

    provider: str
    count: int
    proxies: list[ProxyEndpoint]
    note: str | None = None

    @classmethod
    def from_endpoints(
        cls, provider: str, proxies: list[ProxyEndpoint], note: str | None = None
    ) -> ProxyListResult:
        return cls(provider=provider, count=len(proxies), proxies=proxies, note=note)


class BalanceInfo(BaseModel):
    """Account balance / remaining allowance for a provider."""

    provider: str
    balance: float | None = Field(default=None, description="Monetary balance, if applicable.")
    currency: str | None = None
    traffic_remaining_gb: float | None = Field(
        default=None, description="Remaining traffic allowance in GB, if applicable."
    )
    raw: dict | None = Field(default=None, description="Provider-native payload for reference.")


class UsageInfo(BaseModel):
    """Traffic / request usage for a provider."""

    provider: str
    traffic_used_gb: float | None = None
    traffic_total_gb: float | None = None
    requests_used: int | None = None
    period: str | None = None
    raw: dict | None = None


class Country(BaseModel):
    code: str | None = None
    name: str | None = None
    available_count: int | None = Field(
        default=None, description="Available IPs/nodes in this country, if reported."
    )


class CountryListResult(BaseModel):
    provider: str
    count: int
    countries: list[Country]


class ProviderCapabilities(BaseModel):
    """Static description of what a provider supports."""

    name: str
    display_name: str
    country_of_origin: str | None = None
    website: str
    proxy_types: list[ProxyType]
    operations: list[Operation]
    requires_credentials: list[str] = Field(
        default_factory=list,
        description="Environment variable names the adapter needs to be configured.",
    )
    configured: bool = False
    notes: str | None = None


class ScrapeResult(BaseModel):
    """Result of a managed scraping-API request."""

    provider: str
    url: str
    status_code: int | None = None
    content: str | None = None
    cost: float | None = None
    raw_headers: dict | None = None
