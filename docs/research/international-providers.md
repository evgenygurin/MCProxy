# International / Global Proxy Providers — Research Report

**Prepared:** 2026-06-22
**Purpose:** Inform the MCProxy adapter design. Focus is on each provider's
public REST API surface (what can be automated), auth scheme, and proxy types.
Pricing is approximate and changes frequently — verify against live pages.

## API-readiness summary

| Provider | API base URL | Auth | List/Generate | Buy/Order | Balance/Usage | Sub-users |
|---|---|---|---|:--:|:--:|:--:|
| **Webshare** | `https://proxy.webshare.io/api/v2/` | `Authorization: Token` | ✅ list + config | – | ✅ | ✅ |
| **IPRoyal** | `https://resi-api.iproyal.com/v1` (+ `apid.iproyal.com/v1/reseller`) | Bearer / `X-Access-Token` | ✅ generate-proxy-list | ✅ (DC reseller) | ✅ `/residential/me` | ✅ |
| **Bright Data** | `https://api.brightdata.com` | Bearer | ✅ zone + IP mgmt | ✅ | ✅ richest | via Proxy Manager |
| **Oxylabs** | `https://residential-api.oxylabs.io/v2` | Basic→JWT | DC/HB discovery | – | ✅ stats | ✅ full CRUD |
| **Decodo (Smartproxy)** | `https://api.decodo.com/v1/` | `POST /auth/`→token | ✅ endpoints | – | ✅ subscriptions | ✅ full CRUD |
| **SOAX** | `https://partner.api.soax.com/v1` | `api-key:` header | targeting + IP slots | – | limited | limited (≤5) |
| **NetNut** | `https://customers-api.netnut.io/v1` | login→24h Bearer | endpoint generator | – | ✅ usage | ✅ GB+IP alloc |
| **Proxy-Cheap** | `https://docs.proxy-cheap.com` | API key + secret | ✅ list | ✅ **order()** | ✅ balance() | – |
| **ProxyMesh** | `https://proxymesh.com` | Basic + Bearer | ✅ proxies/geoips | – | per sub-acct | ✅ full CRUD |
| **Infatica** | `https://dashboard.infatica.io/includes/api/client/` | email+pass / `X-API-Key` | gateway params | – | ✅ traffic/balance | – |
| **ScraperAPI** | `https://api.scraperapi.com` | `api_key` param | scrape + DataPipeline | – | ✅ `/account` | – |
| **ScrapingBee** | `https://app.scrapingbee.com/api/v1` | Bearer / `api_key` | scrape | – | ✅ `/usage` | – |
| **Zyte** | `https://api.zyte.com/v1/extract` | Basic (key as user) | scrape/proxy mode | – | Stats API | – |
| **Asocks** | `https://api.asocks.com/v2` | `?apikey=` / Bearer | ✅ ports | ✅ (port) | ✅ `/plan/info` | – |
| **Rayobyte** | not published | key (dashboard) | reseller (gated) | reseller | – | reseller |
| **GeoSurf** | **DEFUNCT (shut down 2023-12-20)** | – | – | – | – | – |
| **Storm Proxies** | **no API** (IP whitelist only) | – | – | – | – | – |
| **PacketStream** | reseller API only | Bearer | gateway params | – | reseller | reseller |

## Key per-provider API facts

### Webshare — `https://proxy.webshare.io/api/v2/`
Auth `Authorization: Token <key>`. Clean REST. `GET /proxy/list/?mode=direct` (proxy
objects: `proxy_address, port, username, password, country_code, city_name, valid`),
`GET /proxy/config/`, `GET /subscription/`, `GET /profile/`, proxy stats, sub-users,
API-key management. Free tier (10 proxies / 1 GB). **Implemented in MCProxy.**

### IPRoyal — `https://resi-api.iproyal.com/v1`
Residential: Bearer. `GET /access/countries`, `GET /access/entry-nodes`,
`POST /access/generate-proxy-list` (body: `format, hostname, port, rotation
(sticky|random), location (_country-xx_city-…), proxy_count, lifetime`),
`GET /residential/me` (`available_traffic` in GB). Datacenter/ISP on
`apid.iproyal.com/v1/reseller` with `X-Access-Token` and full order CRUD
(`POST /orders`, `/orders/{id}/extend`). Traffic never expires. **Implemented.**

### Bright Data — `https://api.brightdata.com`
Bearer. Account Management API: zones (`Add_a_Zone`, `Get_active_Zones`), static IP
add/remove/refresh, `GET /customer/balance`, bandwidth/cost stats, allow/deny lists.
Sub-user routing via self-hosted Proxy Manager (port 22999). Deepest billing API.

### Oxylabs — `https://residential-api.oxylabs.io/v2`
`POST /login` (Basic) → `user_id` + JWT (~1 h). Sub-user CRUD
`/users/{userId}/sub-users`, usage `/client-stats`. Dashboard API on
`api.oxylabs.io` with Bearer key.

### Decodo / Smartproxy — `https://api.decodo.com/v1/`
`POST /auth/` → token. Sub-user CRUD `users/:userId/sub-users`, `GET endpoints`,
whitelists, `GET users/:userId/subscriptions`. Rebranded Smartproxy → Decodo.

### SOAX — `https://partner.api.soax.com/v1`
`api-key:` header. IP-slot mgmt (`/account/package/<key>/ip-list`, `update-ip`,
`detach-ip`), targeting metadata (cities/regions/carriers/ISPs). Proxy access via
`proxy.soax.com:5000`. Balance/usage mostly dashboard.

### NetNut — `https://customers-api.netnut.io/v1`
`POST /auth/login` (email+pass) → 24 h Bearer. `POST /customer/usage/`, traffic/geo
endpoints, sub-user CRUD with GB + IP allocation, Unblocker at `unblocker.netnut.io`.

### Proxy-Cheap — `https://docs.proxy-cheap.com`
API key + secret. SDK methods: `balance()`, `proxies()`, `proxy(id)`,
`whitelist()`, `extend()`, `buyBandwidth()`, `autoExtend()`, `configuration()`,
**`order()`** (programmatic purchase). Network types MOBILE/DATACENTER/RESIDENTIAL/
RESIDENTIAL_STATIC.

### ProxyMesh — `https://proxymesh.com`
Basic + Bearer. `GET /api/proxies/`, `GET /api/geoips/open/`, sub-account CRUD
`/api/sub/*` (bandwidth in `GET /api/sub/get/`), IP-auth `/api/ip/*`. **Implemented.**

### ScraperAPI / ScrapingBee / Zyte (scraping APIs)
- ScraperAPI: `GET /?api_key=&url=&render=&country_code=&premium=`; `GET /account`
  (usage); DataPipeline CRUD. **Implemented.**
- ScrapingBee: `GET /api/v1/?api_key=&url=&render_js=&premium_proxy=&country_code=`;
  `GET /api/v1/usage`. Bearer or `api_key`. **Implemented.**
- Zyte: `POST /v1/extract` (Basic, key as username); proxy mode `api.zyte.com:8011`.

### Asocks — `https://api.asocks.com/v2`
`?apikey=`. `GET /plan/info` (plan + balance), port create/list, locations.
Residential/mobile PAYG ($3/GB). **Implemented (balance).**

### Excluded
- **GeoSurf** — permanently shut down 2023-12-20 (lost patent suit vs Bright Data).
- **Storm Proxies** — no API at all (IP whitelist only); cannot integrate.
- **PacketStream** — only a white-label Reseller API; no end-user management API.
- **Rayobyte** — reseller API exists but undocumented publicly (contact sales).

## Sources
Bright Data: docs.brightdata.com/api-reference · Oxylabs: developers.oxylabs.io ·
Decodo: help.decodo.com/reference, github.com/Decodo/Decodo-API · SOAX:
docs.soax.com, helpcenter.soax.com · Webshare: apidocs.webshare.io · IPRoyal:
docs.iproyal.com · NetNut: help.netnut.io · Proxy-Cheap: docs.proxy-cheap.com,
github.com/proxy-cheap/proxycheap-node · ProxyMesh: docs.proxymesh.com · Infatica:
infatica.io/documentation · ScraperAPI: docs.scraperapi.com · ScrapingBee:
scrapingbee.com/documentation · Zyte: docs.zyte.com · Asocks:
api.asocks.com/v2/swagger/docs · Nimble: docs.nimbleway.com · GeoSurf shutdown:
proxyscrape.com/geosurf-shutting-down.
