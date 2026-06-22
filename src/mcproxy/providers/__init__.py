"""Provider adapters and the provider registry."""

from __future__ import annotations

from ..models import ProviderCapabilities
from .asocks import AsocksProvider
from .base import BaseProvider, OperationNotSupported, ProviderError, ProviderNotConfigured
from .catalog import planned_catalog
from .fineproxy import FineProxyProvider
from .iproyal import IPRoyalProvider
from .proxy6 import Proxy6Provider
from .proxyline import ProxyLineProvider
from .proxymesh import ProxyMeshProvider
from .proxyseller import ProxySellerProvider
from .proxystore import ProxyStoreProvider
from .scraperapi import ScraperAPIProvider
from .scrapingbee import ScrapingBeeProvider
from .webshare import WebshareProvider

#: Adapter classes with working API implementations.
IMPLEMENTED: list[type[BaseProvider]] = [
    # International
    WebshareProvider,
    IPRoyalProvider,
    ProxyMeshProvider,
    ScraperAPIProvider,
    ScrapingBeeProvider,
    # Russian / CIS
    Proxy6Provider,
    ProxyLineProvider,
    ProxyStoreProvider,
    ProxySellerProvider,
    AsocksProvider,
    FineProxyProvider,
]


class Registry:
    """Holds provider instances and exposes lookup + capability listing."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {
            cls.name: cls() for cls in IMPLEMENTED
        }

    def names(self) -> list[str]:
        return sorted(self._providers)

    def get(self, name: str) -> BaseProvider:
        provider = self._providers.get(name.lower().strip())
        if provider is None:
            available = ", ".join(self.names())
            raise ProviderError(
                f"Unknown provider '{name}'. Implemented providers: {available}."
            )
        return provider

    def capabilities(self, configured_only: bool = False) -> list[ProviderCapabilities]:
        caps = [p.capabilities() for p in self._providers.values()]
        if configured_only:
            caps = [c for c in caps if c.configured]
        else:
            caps += planned_catalog()
        return sorted(caps, key=lambda c: (not c.configured, c.name))


_registry: Registry | None = None


def get_registry() -> Registry:
    global _registry
    if _registry is None:
        _registry = Registry()
    return _registry


__all__ = [
    "IMPLEMENTED",
    "BaseProvider",
    "OperationNotSupported",
    "ProviderError",
    "ProviderNotConfigured",
    "Registry",
    "get_registry",
]
