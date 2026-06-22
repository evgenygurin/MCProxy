"""Base class and shared contract for all proxy provider adapters."""

from __future__ import annotations

import httpx

from ..config import get_credential
from ..http import build_client
from ..models import (
    BalanceInfo,
    Country,
    CountryListResult,
    GeoTarget,
    Operation,
    ProviderCapabilities,
    ProxyEndpoint,
    ProxyListResult,
    ProxyProtocol,
    ProxyType,
    Rotation,
    ScrapeResult,
    UsageInfo,
)


class ProviderError(Exception):
    """Generic provider failure surfaced to the agent as a tool error."""


class ProviderNotConfigured(ProviderError):
    """Raised when an operation is attempted without the required credentials."""


class OperationNotSupported(ProviderError):
    """Raised when a provider does not implement a requested operation."""


class BaseProvider:
    """Base adapter mapping one provider's API onto the unified models.

    Subclasses set the class attributes below and override the operations they
    support. Unimplemented operations raise :class:`OperationNotSupported`, which
    the generic tools turn into a clear message for the agent.
    """

    name: str = ""
    display_name: str = ""
    website: str = ""
    country_of_origin: str | None = None
    proxy_types: list[ProxyType] = []
    operations: list[Operation] = []
    credential_env: list[str] = []
    notes: str | None = None

    # ----- configuration -------------------------------------------------

    def credential(self, *names: str) -> str | None:
        return get_credential(*(names or self.credential_env))

    def is_configured(self) -> bool:
        """True if at least the primary credential is present."""
        if not self.credential_env:
            return True
        return self.credential(self.credential_env[0]) is not None

    def require_credential(self, *names: str) -> str:
        value = self.credential(*names)
        if not value:
            wanted = ", ".join(names or self.credential_env)
            raise ProviderNotConfigured(
                f"{self.display_name} is not configured. Set one of: {wanted}."
            )
        return value

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            name=self.name,
            display_name=self.display_name,
            country_of_origin=self.country_of_origin,
            website=self.website,
            proxy_types=self.proxy_types,
            operations=self.operations,
            requires_credentials=self.credential_env,
            configured=self.is_configured(),
            notes=self.notes,
        )

    # ----- HTTP helper ---------------------------------------------------

    def client(
        self,
        base_url: str = "",
        headers: dict[str, str] | None = None,
        auth: httpx.Auth | tuple[str, str] | None = None,
    ) -> httpx.AsyncClient:
        return build_client(base_url=base_url, headers=headers, auth=auth)

    # ----- operations (override as supported) ----------------------------

    async def list_proxies(
        self,
        proxy_type: ProxyType | None = None,
        country: str | None = None,
        limit: int = 100,
    ) -> ProxyListResult:
        raise OperationNotSupported(
            f"{self.display_name} does not support listing existing proxies via API."
        )

    async def generate_proxy_list(
        self,
        proxy_type: ProxyType,
        geo: GeoTarget,
        count: int = 1,
        rotation: Rotation = Rotation.ROTATING,
        session_duration: str | None = None,
        protocol: ProxyProtocol = ProxyProtocol.HTTP,
    ) -> ProxyListResult:
        raise OperationNotSupported(
            f"{self.display_name} does not support proxy-list generation via API."
        )

    async def check_balance(self) -> BalanceInfo:
        raise OperationNotSupported(
            f"{self.display_name} does not expose balance via API."
        )

    async def get_usage(self) -> UsageInfo:
        raise OperationNotSupported(
            f"{self.display_name} does not expose usage via API."
        )

    async def list_countries(self, proxy_type: ProxyType | None = None) -> CountryListResult:
        raise OperationNotSupported(
            f"{self.display_name} does not expose targetable countries via API."
        )

    async def buy_proxies(
        self,
        proxy_type: ProxyType,
        quantity: int,
        country: str | None = None,
        period_days: int | None = None,
        protocol: ProxyProtocol = ProxyProtocol.HTTP,
        extra: dict | None = None,
    ) -> ProxyListResult:
        raise OperationNotSupported(
            f"{self.display_name} does not support purchasing proxies via API."
        )

    async def extend_proxies(self, proxy_ids: list[str], period_days: int) -> dict:
        raise OperationNotSupported(
            f"{self.display_name} does not support extending proxies via API."
        )

    async def scrape(
        self,
        url: str,
        render_js: bool = False,
        country: str | None = None,
        premium: bool = False,
    ) -> ScrapeResult:
        raise OperationNotSupported(
            f"{self.display_name} does not provide a managed scraping API."
        )

    # convenience for adapters
    @staticmethod
    def _country(code: str | None = None, name: str | None = None, count: int | None = None) -> Country:
        return Country(code=code, name=name, available_count=count)

    @staticmethod
    def _endpoint(**kwargs) -> ProxyEndpoint:
        return ProxyEndpoint(**kwargs)
