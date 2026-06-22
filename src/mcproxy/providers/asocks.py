"""ASOCKS adapter (asocks.com).

Docs: https://api.asocks.com/v2/swagger/docs
Base URL: https://api.asocks.com/v2/
Auth: API key as query param ``?apikey=`` (also accepts ``Authorization: Bearer``).

Residential + mobile, pay-as-you-go per GB. Confirmed endpoint ``GET /plan/info``
returns plan + balance; port/list/location endpoints live in the Swagger UI.
"""

from __future__ import annotations

from typing import Any

from ..http import as_float, json_or_raise
from ..models import BalanceInfo, Operation, ProxyType
from .base import BaseProvider

BASE_URL = "https://api.asocks.com/v2"


class AsocksProvider(BaseProvider):
    name = "asocks"
    display_name = "ASOCKS"
    website = "https://asocks.com"
    country_of_origin = "RU"  # popular in RU/CIS; operator IP Security LTD (BVI)
    proxy_types = [ProxyType.RESIDENTIAL, ProxyType.MOBILE]
    operations = [Operation.CHECK_BALANCE]
    credential_env = ["ASOCKS_API_KEY"]
    notes = "Residential/mobile PAYG ($3/GB). Port creation lives in the Swagger API."

    async def check_balance(self) -> BalanceInfo:
        async with self.client(base_url=BASE_URL) as client:
            data = json_or_raise(
                await client.get("/plan/info", params={"apikey": self.require_credential()})
            )
        payload: dict[str, Any] = data.get("message", data) if isinstance(data, dict) else {}
        balance = payload.get("balance") if isinstance(payload, dict) else None
        return BalanceInfo(
            provider=self.name,
            balance=as_float(balance),
            currency="USD",
            raw=data if isinstance(data, dict) else None,
        )
