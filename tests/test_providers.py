from __future__ import annotations

import httpx
import pytest
import respx

from mcproxy.models import ProxyType, Rotation
from mcproxy.providers import get_registry


@pytest.fixture
def registry():
    return get_registry()


@respx.mock
async def test_proxy6_check_balance(registry, monkeypatch):
    monkeypatch.setenv("PROXY6_API_KEY", "testkey")
    respx.route(method="GET", url__regex=r"px6\.link/api/testkey/getcountry").mock(
        return_value=httpx.Response(
            200, json={"status": "yes", "balance": "123.45", "currency": "RUB", "list": ["ru", "us"]}
        )
    )
    bal = await registry.get("proxy6").check_balance()
    assert bal.balance == pytest.approx(123.45)
    assert bal.currency == "RUB"


@respx.mock
async def test_proxy6_error_envelope(registry, monkeypatch):
    from mcproxy.providers import ProviderError

    monkeypatch.setenv("PROXY6_API_KEY", "testkey")
    respx.route(method="GET", url__regex=r"px6\.link").mock(
        return_value=httpx.Response(200, json={"status": "no", "error_id": 100, "error": "Auth error"})
    )
    with pytest.raises(ProviderError, match="Auth error"):
        await registry.get("proxy6").check_balance()


@respx.mock
async def test_webshare_list_proxies(registry, monkeypatch):
    monkeypatch.setenv("WEBSHARE_API_KEY", "wskey")
    respx.route(method="GET", url__regex=r"proxy\.webshare\.io/api/v2/proxy/list").mock(
        return_value=httpx.Response(
            200,
            json={
                "count": 1,
                "results": [
                    {
                        "proxy_address": "1.2.3.4",
                        "port": 8080,
                        "username": "u",
                        "password": "p",
                        "country_code": "US",
                        "city_name": "Ashburn",
                    }
                ],
            },
        )
    )
    result = await registry.get("webshare").list_proxies(limit=10)
    assert result.count == 1
    proxy = result.proxies[0]
    assert proxy.url == "http://u:p@1.2.3.4:8080"
    assert proxy.country == "US"


@respx.mock
async def test_iproyal_generate_proxy_list(registry, monkeypatch):
    monkeypatch.setenv("IPROYAL_API_TOKEN", "iptoken")
    respx.route(method="POST", url__regex=r"resi-api\.iproyal\.com/v1/access/generate-proxy-list").mock(
        return_value=httpx.Response(
            200,
            json=[
                "geo.iproyal.com:12321:user1:pass_session-abc_lifetime-2h",
                "geo.iproyal.com:12321:user2:pass_session-xyz_lifetime-2h",
            ],
        )
    )
    result = await registry.get("iproyal").generate_proxy_list(
        proxy_type=ProxyType.RESIDENTIAL,
        geo=__import__("mcproxy.models", fromlist=["GeoTarget"]).GeoTarget(country="US"),
        count=2,
        rotation=Rotation.STICKY,
        session_duration="2h",
    )
    assert result.count == 2
    assert result.proxies[0].host == "geo.iproyal.com"
    assert result.proxies[0].port == 12321
    assert result.proxies[0].username == "user1"
    assert result.proxies[0].rotation == Rotation.STICKY


@respx.mock
async def test_scraperapi_scrape(registry, monkeypatch):
    monkeypatch.setenv("SCRAPERAPI_API_KEY", "sakey")
    respx.route(method="GET", url__regex=r"api\.scraperapi\.com").mock(
        return_value=httpx.Response(200, text="<html>ok</html>", headers={"sa-credit-cost": "5"})
    )
    result = await registry.get("scraperapi").scrape("https://example.com", render_js=True)
    assert result.status_code == 200
    assert "<html>" in (result.content or "")
    assert result.cost == 5.0


@respx.mock
async def test_proxymesh_list_proxies(registry, monkeypatch):
    monkeypatch.setenv("PROXYMESH_USERNAME", "user")
    monkeypatch.setenv("PROXYMESH_PASSWORD", "pw")
    respx.route(method="GET", url__regex=r"proxymesh\.com/api/proxies").mock(
        return_value=httpx.Response(
            200, json={"proxies": ["us-wa.proxymesh.com:31280", "fr.proxymesh.com:31280"]}
        )
    )
    result = await registry.get("proxymesh").list_proxies()
    assert result.count == 2
    assert result.proxies[0].host == "us-wa.proxymesh.com"
    assert result.proxies[0].port == 31280


@respx.mock
async def test_webshare_check_balance_empty_results(registry, monkeypatch):
    # Regression: empty results must not raise IndexError.
    monkeypatch.setenv("WEBSHARE_API_KEY", "wskey")
    respx.route(method="GET", url__regex=r"proxy\.webshare\.io/api/v2/subscription").mock(
        return_value=httpx.Response(200, json={"count": 0, "results": []})
    )
    bal = await registry.get("webshare").check_balance()
    assert bal.provider == "webshare"
    assert bal.raw == {"count": 0, "results": []}


@respx.mock
async def test_proxy6_list_tolerates_missing_port(registry, monkeypatch):
    # Regression: a proxy item without a numeric port must not crash.
    monkeypatch.setenv("PROXY6_API_KEY", "testkey")
    respx.route(method="GET", url__regex=r"px6\.link/api/testkey/getproxy").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "yes",
                "balance": "1",
                "list": {"1": {"ip": "1.2.3.4", "host": "1.2.3.4", "user": "u", "pass": "p"}},
            },
        )
    )
    result = await registry.get("proxy6").list_proxies()
    assert result.count == 1
    assert result.proxies[0].port == 0


def test_as_float_helper():
    from mcproxy.http import as_float

    assert as_float("12.5") == 12.5
    assert as_float(3) == 3.0
    assert as_float(None) is None
    assert as_float("not-a-number") is None


async def test_operation_not_supported(registry, monkeypatch):
    from mcproxy.providers import OperationNotSupported

    monkeypatch.setenv("SCRAPERAPI_API_KEY", "sakey")
    # ScraperAPI is a scraping API; it doesn't list proxies.
    with pytest.raises(OperationNotSupported):
        await registry.get("scraperapi").list_proxies()
