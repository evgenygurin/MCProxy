"""FineProxy adapter (fineproxy.org).

Docs: https://api.fineproxy.org/docs
Base URL: https://api.fineproxy.org
Auth: HTTP Basic (email:password).
"""

from __future__ import annotations

from ..config import get_credential
from ..http import as_float, json_or_raise
from ..models import BalanceInfo, Operation, ProxyType
from .base import BaseProvider, ProviderNotConfigured

BASE_URL = "https://api.fineproxy.org"


class FineProxyProvider(BaseProvider):
    name = "fineproxy"
    display_name = "FineProxy"
    website = "https://fineproxy.org"
    country_of_origin = "RU"
    proxy_types = [ProxyType.DATACENTER, ProxyType.ISP, ProxyType.RESIDENTIAL]
    operations = [Operation.CHECK_BALANCE]
    credential_env = ["FINEPROXY_EMAIL", "FINEPROXY_PASSWORD"]
    notes = "Veteran RU brand; per-IP datacenter/ISP with unlimited traffic. Basic auth."

    def is_configured(self) -> bool:
        return bool(get_credential("FINEPROXY_EMAIL") and get_credential("FINEPROXY_PASSWORD"))

    def _auth(self) -> tuple[str, str]:
        email = get_credential("FINEPROXY_EMAIL")
        password = get_credential("FINEPROXY_PASSWORD")
        if not email or not password:
            raise ProviderNotConfigured("FineProxy needs FINEPROXY_EMAIL and FINEPROXY_PASSWORD.")
        return email, password

    async def check_balance(self) -> BalanceInfo:
        async with self.client(base_url=BASE_URL, auth=self._auth()) as client:
            data = json_or_raise(await client.get("/api/billing/credit"))
        balance = data.get("credit") if isinstance(data, dict) else data
        return BalanceInfo(
            provider=self.name,
            balance=as_float(balance),
            currency="USD",
            raw=data if isinstance(data, dict) else {"credit": data},
        )
