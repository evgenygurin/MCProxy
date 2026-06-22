# Providers

MCProxy normalizes many proxy vendors behind one interface. This page is the
curated overview; the full research (API endpoints, pricing, reputation, sources)
lives in [`research/international-providers.md`](research/international-providers.md)
and [`research/russian-cis-providers.md`](research/russian-cis-providers.md).

## Implemented adapters

| Provider | Env vars | Auth style | Notable operations |
|---|---|---|---|
| Webshare | `WEBSHARE_API_KEY` | `Authorization: Token` | list, balance, usage, countries |
| IPRoyal | `IPROYAL_API_TOKEN` | Bearer | generate-proxy-list, balance, countries |
| ProxyMesh | `PROXYMESH_USERNAME`, `PROXYMESH_PASSWORD` | HTTP Basic | list, countries, usage |
| ScraperAPI | `SCRAPERAPI_API_KEY` | `api_key` param | scrape, usage |
| ScrapingBee | `SCRAPINGBEE_API_KEY` | Bearer / param | scrape, usage |
| Proxy6 | `PROXY6_API_KEY` | key in URL path | list, balance, countries, buy, extend |
| ProxyLine | `PROXYLINE_API_KEY` | `API-KEY` header | list, balance, countries, buy, extend |
| Proxy-Store | `PROXYSTORE_API_KEY` | key in URL path | list, balance, countries, buy, extend |
| Proxy-Seller | `PROXYSELLER_API_KEY` | key in URL path | list, balance, countries |
| ASOCKS | `ASOCKS_API_KEY` | `apikey` param | balance |
| FineProxy | `FINEPROXY_EMAIL`, `FINEPROXY_PASSWORD` | HTTP Basic | balance |

## Planned adapters (surfaced by `list_providers`)

These have public REST APIs documented in the research files; adapters are not yet
implemented. Contributions welcome.

**Global:** Bright Data, Oxylabs, Decodo (Smartproxy), SOAX, NetNut, Infatica,
Proxy-Cheap, Zyte, Nimble, Rayobyte.

**Russian / CIS:** Mobile Proxy Space, iProxy.online, ProxyMarket, Froxy.

## Auth patterns

Adapters template a few recurring schemes:

1. **Key in URL path** — `{base}/api/{key}/{method}` (Proxy6, Proxy-Store, Proxy-Seller).
2. **Header token** — `Authorization: Token/Bearer` or `API-KEY` (Webshare, IPRoyal, ProxyLine).
3. **Query param key** — `?api_key=` / `?apikey=` (ScraperAPI, ScrapingBee, ASOCKS).
4. **HTTP Basic** — `email:password` or `user:password` (FineProxy, ProxyMesh).

## Adding a provider

1. Create `src/mcproxy/providers/<name>.py` subclassing `BaseProvider`.
2. Set the class attributes (`name`, `display_name`, `website`, `proxy_types`,
   `operations`, `credential_env`) and override only the operations the API supports.
3. Map the vendor response onto the shared models in `models.py`.
4. Register the class in `IMPLEMENTED` in `src/mcproxy/providers/__init__.py`.
5. Add the env vars to `.env.example` and a test in `tests/test_providers.py`.

See `webshare.py` (header token) and `proxy6.py` (key-in-URL) as references.

> **Excluded by design:** GeoSurf (defunct since 2023-12-20), Storm Proxies (no API),
> and RSocks (seized/dead) are intentionally not integrated.
