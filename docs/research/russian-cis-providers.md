# Russian / CIS Proxy-Selling Providers — Research Report

**Prepared:** 2026-06-22
**Purpose:** Inform the design of an MCP server that programmatically connects to RU/CIS proxy providers' APIs (buy, list/export, prolong/extend, balance, list countries).
**Research method:** Parallel web research in Russian and English; direct fetches of API documentation and SDK READMEs where reachable. Several RU doc sites (docs.proxy-seller.com, proxys.io/api, api.dashboard.proxy.market) block automated fetches (403/503/JS-rendered) — for those, endpoint sets were corroborated from search indexing and official GitHub SDKs and are flagged accordingly.

---

## TL;DR for the MCP build

**Tier 1 — clean, fully documented public REST APIs (build first):**

| Provider | Why | Auth pattern |
|---|---|---|
| **Proxy6** (proxy6.net) | Verbatim-verified docs, simple, RUB, covers buy/list/prolong/check/countries/balance | API key **in URL path** |
| **Proxy-Seller** (proxy-seller.com) | Broadest product set, official SDKs (PHP/Py/Node/Java/Go), calc→make flow | API key **in URL path** |
| **ProxyLine** (proxyline.net) | Cleanest classic REST, every CRUD endpoint documented | `api_key` query **or** `API-KEY` header |
| **Proxy-Store** (proxy-store.com) | Same shape as Proxy6 but with residential/mobile + `getbalance` | API key **in URL path** |
| **FineProxy** (fineproxy.org) | Full docs with Postman, basic-auth, IP export | HTTP **Basic** (email:password) |
| **iProxy.online** | Richest mobile API (rotation, SMS, ACLs, action links) | **Bearer** token |
| **Mobile Proxy Space** (mobileproxy.space) | Command API + official SDKs + no-auth rotate link | **Bearer** token |
| **ASOCKS** (asocks.com) | Swagger REST, residential/mobile, geo | API key **query param** `?apikey=` |

**Tier 2 — API exists but docs gated / not publicly enumerable (confirm in-dashboard before coding):**
ProxyMarket (proxy.market, Swagger behind JS), Proxys.io (key-based, no public REST reference), Froxy (gateway + dashboard API), LTESocks (docs in dashboard), Proxy-Sale/Geonix (uses the Proxy-Seller platform).

**Tier 3 — no public API / avoid:**
AdvancedProxy (dashboard only), BeeProxy (merged into 9Proxy, no API), Local-IP (could not verify the brand/domain), RSocks (**seized by FBI in 2022 — dead, do not integrate**).

**Two dominant auth patterns to template in the MCP server:**
1. **Key-in-URL-path** — Proxy6, Proxy-Store, Proxy-Seller (`.../api/{key}/...`).
2. **Header token** — iProxy & Mobile Proxy Space (Bearer), ProxyLine (`API-KEY`), ASocks (`?apikey=`), FineProxy (Basic).

---

## Comparison table

| Provider | Website | Proxy types | Public REST API | API docs URL | Auth | API: buy | list/export | prolong | balance | countries | Currency |
|---|---|---|---|---|---|:--:|:--:|:--:|:--:|:--:|---|
| Proxy6 | proxy6.net | IPv4, IPv4-shared, IPv6, MTProto | ✅ verified | proxy6.net/developers | key in URL path | ✅ | ✅ | ✅ | ✅ (every resp) | ✅ | RUB/USD |
| Proxy-Seller | proxy-seller.com | IPv4, IPv6, ISP, Residential, Mobile, Mix | ✅ + SDKs | docs.proxy-seller.com | key in URL path | ✅ | ✅ | ✅ | ✅ | ✅ | USD (RUB on .ru) |
| ProxyLine | proxyline.net | IPv4, IPv6 (dc), MTProto | ✅ verified | proxyline.net/api | `api_key` param / `API-KEY` hdr | ✅ | ✅ | ✅ | ✅ | ✅ | RUB/USD/UAH/KZT/EUR |
| Proxy-Store | proxy-store.com | IPv4, IPv6, Residential, Mobile | ✅ verified | proxy-store.com/en/developers | key in URL path | ✅ | ✅ | ✅ | ✅ | ✅ | USD |
| FineProxy | fineproxy.org | IPv4 dc, ISP, dedicated, rotating residential | ✅ verified | api.fineproxy.org/docs | HTTP Basic | ✅ | ✅ | ✅(sticky/ttl) | ✅ | — | USD |
| Proxys.io | proxys.io | IPv4, IPv6, Residential, Mobile | ⚠️ key-based, no public REST ref | proxys.io/api (gated) | personal API key | ? | ✅ (TXT, static) | ? | ? | ? | USD |
| Froxy | froxy.com | Residential, Mobile, Datacenter | ⚠️ gateway + dashboard API | froxy.com/en/api | user:pass in URL; geo in pwd | dash | gateway | dash | dash | pwd code | USD |
| ProxyMarket | proxy.market | IPv4, IPv6, rotating dc, ISP, Residential, Mobile | ⚠️ Swagger (JS-rendered) | api.dashboard.proxy.market/docs | API token | ✅ | ✅ | ✅ | likely | ✅ | USD |
| Proxy-Sale → Geonix | proxy-sale.com → geonix.com | IPv4, IPv6, ISP, Mobile, Residential | ✅ (Proxy-Seller platform) | docs.proxy-seller.com | key in URL path | ✅ | ✅ | ✅ | ✅ | ✅ | USD |
| ASOCKS | asocks.com | Residential, Mobile | ✅ Swagger | api.asocks.com/v2/swagger/docs | `?apikey=` query | ✅(port) | ✅ | ✅(rotate) | ✅ | ✅(geo) | USD |
| iProxy.online | iproxy.online | Mobile (DIY phones) | ✅ richest | iproxy.online/docs-api-connection | Bearer token | n/a (subscription) | ✅ | ✅ rotate | ✅ | sim-based | USD/RUB |
| Mobile Proxy Space | mobileproxy.space | Mobile 3G/4G/5G | ✅ + SDKs | mobileproxy.space/api.html | Bearer token | ✅ | ✅ | ✅ | ✅ | ✅+operators | RUB |
| LTESocks | ltesocks.io | ISP, IPv4, IPv6, Mobile 4G/5G | ⚠️ docs gated | in dashboard | API key (dashboard) | ? | ✅ | ✅ rotate | ? | ✅ | USD |
| AdvancedProxy | advanced.name | IPv4 HTTP/SOCKS, backconnect rotating | ❌ none | — | — | — | — | — | — | — | USD/RUB |
| BeeProxy → 9Proxy | 9proxy.com | Residential IPv4 | ❌ none found | — | — | — | — | — | — | — | USD |
| Local-IP | (unverified) | (mobile?) | ❓ unverified | — | — | — | — | — | — | — | — |
| RSocks | rsocks.net | — | ❌ **SEIZED/DEAD** | — | — | — | — | — | — | — | — |

---

# Tier 1 — fully documented public REST APIs

## 1. Proxy6 (proxy6.net) — VERIFIED

- **Sites:** https://proxy6.net (primary, Russian), `/en/` for English, mirror https://px6.me, **API host https://px6.link**. Operating since 2011/2016.
- **Proxy types:** Individual/private IPv4, shared IPv4, IPv6, and MTProto (Telegram). Protocols HTTP/HTTPS, SOCKS5, or auto. Country-level geo only. **No residential or mobile.** Known as the cheap IPv6 specialist.
- **Pricing (RUB primary, USD optional):** IPv6 from ~3.6 RUB / 1 proxy / 3 days (bulk down to ~1.2 RUB); IPv4 ~69.9 RUB/IP (under 100 qty), ~60 RUB/IP at 100+.
- **Reputation:** Long-running budget leader; consistently #1–#4 in RU rankings (ecomservice.ru 4.9). Popular with affiliate/arbitrage. Many community wrappers (PHP/Py/JS).

### API CAPABILITIES (verified from proxy6.net/developers)
- **Base URL / auth:** `https://px6.link/api/{api_key}/{method}/?{params}` — **API key in the URL path** (generated in account "Developers/API" tab, can be IP-restricted). GET, JSON (UTF-8). **Rate limit: 3 req/sec → HTTP 429.**
- **Version codes:** `3`=IPv4 shared, `4`=IPv4, `5`=MTProto, `6`=IPv6.
- **Balance:** no dedicated endpoint — **every response includes** `status`, `user_id`, `balance`, `currency`. Read it by calling any method.

| Method | Params | Purpose |
|---|---|---|
| `getprice` | count, period, version | Price quote |
| `getcount` | country, version | Stock count per country |
| `getcountry` | version | List available countries (ISO2) |
| `getproxy` | state, descr, page, limit | **List/export your proxies** (state: active/expired/expiring/all; limit≤1000) |
| `buy` | count, period, country, version, descr, auto_prolong | **Buy proxies** |
| `prolong` | period, ids | **Extend/renew** |
| `delete` | ids OR descr | Delete |
| `setdescr` | new + (ids OR old) | Set comment |
| `check` | ids OR proxy | **Validate proxy** (returns proxy_status) |

- **Proxy fields:** id, ip, host, port, user, pass, type, country, date, date_end, unixtime, unixtime_end, descr, active.
- **Errors:** `{"status":"no","error_id":N,"error":"..."}`. Codes: 100 auth, 105 IP not allowed, 200 count, 210 period, 220 country, 240 version, 300 out of stock, 400 low balance, 429 rate limit.

---

## 2. Proxy-Seller (proxy-seller.com / .ru / .me)

- **Sites:** https://proxy-seller.com (English), https://proxy-seller.ru (Russian), redirects from proxy-seller.io/.me. Docs: https://docs.proxy-seller.com. Since 2014. Trustpilot ~4.4–4.7.
- **Proxy types:** IPv4 (dedicated + shared), IPv6, ISP, Residential, Mobile (4G/5G), plus Mix / Mix-ISP. 20M+ IPs, 220+ countries. HTTP/HTTPS, SOCKS5. Residential supports session-ID + TTL, sticky/rotating.
- **Pricing (USD; RUB on .ru):** Residential ~$0.7–3.5/GB PAYG; IPv6 from ~$0.16/IP; IPv4 shared ~$0.60–0.70, dedicated ~$1.00–2.50; ISP ~$1–3; Mobile ~$30–80/mo.
- **Reputation:** Major established CIS + international brand; 24/7 support; multi-language SDKs.

### API CAPABILITIES (docs return 403 to bots; confirmed via search + official GitHub SDKs)
- **Base URL / auth:** `https://proxy-seller.com/personal/api/v1/{YourApiKey}/{resource}/{action}` — **API key in URL path** (from /personal/api/). **Business errors return HTTP 200 with `errors[]`** (not HTTP error codes).
- **Official SDKs:** github.com/proxy-seller → `user-api-python`, `user-api-php`, `user-api-nodejs`, `user-api-java`, `userApiGolang`. PyPI: `proxy-seller-user-api`.
- **Product `type` segment:** `ipv4`, `ipv6`, `isp`, `mobile`, `mix`, `mix_isp`, `resident`.

| Endpoint | Method | Purpose |
|---|---|---|
| `/ping` | GET | Connectivity |
| `/balance` (`/balance/get`) | GET | **Balance** |
| `/balance/add`, `/balance/payments/list` | POST/GET | Add funds, payment systems |
| `/reference/list/{type}` | GET | **Countries (countryId) + period IDs** for ordering |
| `/order/calc/{type}` | POST | **Price quote** |
| `/order/make/{type}` | POST | **Place order / buy** (returns listBaseOrderNumbers) |
| `/prolong/calc`, `/prolong/make` | POST | Quote / **extend** |
| `/proxy/list/{type}` | GET | **List/export proxies** |
| `/proxy/download/{listId}` | GET | Download list file |
| `/proxy/comment/set` | POST | Set comment |
| `/proxy/check` | GET/POST | **Check validity** |
| `/auth/list`, `/auth/active` | GET | IP/login authorizations |
| `/resident/package`, `/resident/geo` | — | Residential packages / geo |
| `/resident/list` (+ rename/delete/rotation) | GET/POST | Manage residential lists & **rotation** |

- **SDK method names (1:1):** `ping, balance, balanceAdd, balancePaymentsList, referenceList, orderCalc/Make{Ipv4,Ipv6,Isp,Mobile,Mix,Resident}, prolongCalc, prolongMake, proxyList, proxyDownload, proxyCommentSet, proxyCheck, residentPackage, residentGeo, residentList, residentListRename, residentListDelete, authList, authActive`. Helpers `setPaymentId(id)` (1=inner balance, 43=card), `setGenerateAuth(Y/N)`.
- **Order flow:** `/reference/list/{type}` → `/order/calc/{type}` → `/order/make/{type}`. (Jan 2024 breaking change removed `targetId`/`targetSectionId`.)
- **Residential geo/rotation:** credential suffixes `xxx_c_US` (country), `xxx_c_US_city_New-York` (city); session-ID + TTL (`s`/`m`/`h`); ports 10000–10999 each = distinct exit IP.

---

## 3. ProxyLine (proxyline.net) — VERIFIED

- **Site:** https://proxyline.net. API host https://panel.proxyline.net. Since mid-2010s.
- **Proxy types:** Dedicated + shared **IPv4** and **IPv6** datacenter proxies; HTTP/SOCKS5 + MTProto. **No mobile/residential.** 150+ countries, 4700+ subnets, city-level selection, IP binding (≤3/order), auto-renew.
- **Pricing (multi-currency: USD, RUB, UAH, KZT, EUR, GBP, crypto):** individual IPv4 ~$1.56–1.77/IP/mo, shared IPv4 from ~$0.99, IPv6 cheapest. Min 1 IP for 5+ days.
- **Reputation:** Long-established, well-regarded for stable cheap datacenter IPs; strong Telegram/MTProto use. Negatives: occasional outages, some 2024 support complaints.

### API CAPABILITIES (verified from proxyline.net/api)
- **Base URL:** `https://panel.proxyline.net/api/`
- **Auth:** `api_key` **query param** OR `API-KEY` **header**. **Rate limit: 50 req/min.**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/proxies/` | **List proxies** (filters: status, type, ip_version, country, dates, orders, format, limit≤2000, offset; export formats txt-http/txt-socks5/custom-*) |
| GET | `/orders/` | List orders (date_after/before) |
| POST | `/renew/` | **Prolong** (proxies, period 5–360d, coupon) |
| POST | `/new-order/` | **Buy** (type, ip_version, country, quantity, period, coupon, ip_list) |
| POST | `/new-order-amount/` | **Price quote** (same params) |
| GET | `/countries/` | **Countries with nested cities** |
| GET | `/ips/` | Available IPs (req: type, ip_version, country; opt city) |
| GET | `/ips-count/` | Count available (≤1000) |
| GET | `/balance/` | **Balance** + affiliate balance |

- Constraints: type = `dedicated`/`shared` (IPv6 dedicated only); ip_version 4/6; period 5–360 in 30-day steps.

---

## 4. Proxy-Store (proxy-store.com) — VERIFIED

- **Site:** https://proxy-store.com. Docs https://proxy-store.com/en/developers. Since ~2016.
- **Proxy types:** Datacenter IPv4/IPv6, Residential, Mobile, categorized (social media, games, general). IP-auth (≤3 IPs), auto-prolong, protocol switching.
- **Pricing:** USD (getbalance returns USD). Per-proxy by quantity/duration/country/category.
- **Reputation:** Established mid/large CIS seller; appears in RU rankings.

### API CAPABILITIES (verified from proxy-store.com/en/developers)
- **Base URL / auth:** `https://proxy-store.com/api/{api_key}/{method}/?{params}` — **API key in URL path** (Proxy6-style shape, but with a dedicated balance method).
- **Responses:** `"status":"ok"` on success; `false` + error id/description on failure; `nokey=1` returns list without keys.

| Method | Purpose |
|---|---|
| `getbalance` | **Account balance** |
| `getcategory` | Proxy categories |
| `getprice` | **Price quote** (count/duration/country) |
| `getcount` | Stock by region |
| `getcountry` | **Countries** |
| `getproxy` | **List proxies** (filterable) |
| `buy` | **Buy** |
| `prolong` / `autoprolong` | **Extend** / auto-renew 30d |
| `delete` | Delete |
| `check` | Validate |
| `setipauth` | IP authorization (≤3) |
| `settype` | HTTP↔SOCKS5 |
| `setdescr` | Comments |

---

## 5. FineProxy (fineproxy.org) — VERIFIED

- **Site:** https://fineproxy.org. Docs https://api.fineproxy.org/docs (with bash/JS/PHP/Python + Postman). Russian team, since 2011.
- **Proxy types:** Datacenter IPv4 (from $0.07/IP), ISP (from $0.25/IP), dedicated (from $2/IP), PPR/rotating residential (sticky sessions). HTTP/HTTPS, SOCKS4/5. Per-IP, unlimited traffic, ~20 locations.
- **Pricing (USD):** "1000 proxies for $89." Accepts RU bank cards incl. SBP. 30-min free trial.
- **Reputation:** Veteran RU brand; frequently cited in RU listicles.

### API CAPABILITIES (verified)
- **Base URL:** `https://api.fineproxy.org`
- **Auth:** **HTTP Basic** — `Authorization: Basic {base64(email:password)}`.

| Endpoint | Purpose |
|---|---|
| `GET /api/clients` | Client info |
| `GET /api/services`, `/api/service/{id}` | Services |
| `PUT /api/service/{id}` | IP binding / password / refresh list |
| `POST /api/product/{pid}` | **Order** |
| `GET /api/products` (+`/orderby/{field}`), `/api/product/{pid}` | Catalog |
| `GET /api/iplist/{type}/{format}/{id}` | **Export proxy list** (CSV/TXT/JSON) |
| `GET /api/billing/credit` | **Balance** |
| `/api/billing/invoices`, `/api/billing/invoice/{id}` | Billing |
| `/api/networkstatus/...`, `/api/stats/{id}`, `/api/rate/{id}` | Status/stats |
| `/api/sticky/list\|rotate\|changettl\|resetall/...` | **Sticky session / rotation control** |

---

## 6. iProxy.online — richest mobile API (VERIFIED)

- **Site:** https://iproxy.online. Docs https://iproxy.online/docs-api-connection. **DIY model:** you supply Android phones + SIMs; iProxy is the management/software layer. Up to 15 ports per phone.
- **Proxy types:** Mobile only (your SIMs determine geo/operator). SOCKS5, HTTP, OpenVPN, UDP.
- **Pricing (USD, RUB accepted):** subscription **per connection/phone** ~$9–12.50/30d ("from $6/mo"), volume discounts; plus your SIM cost. 2-day trial. Not GB-based.
- **Reputation:** The go-to RU/CIS platform for mobile proxy farms; best-in-class API/docs; Dolphin Anty integrations.

### API CAPABILITIES (verified)
- **Base URL:** `https://iproxy.online/api/cn/v1/` (+ `https://iproxy.online/api/console/v1/...` for device commands).
- **Auth:** **Bearer** — `Authorization: Bearer {connection_api_key}` (per-connection key).
- **Endpoints:** connection (`GET /api/cn/v1/`, `POST .../update-basic-info`, `.../update-settings`, `.../change-plan`, team-access modify/remove); **IP rotation** `POST /api/console/v1/connection/{id}/command-push` (commands: reboot, **changeip**, refresh) + `GET /api/cn/v1/ip-history`; proxy access CRUD (`POST/GET .../proxy-access`, `.../{id}/update`, `DELETE .../{id}`); **action links** (shareable rotate/reboot URLs) CRUD; traffic ACLs; OpenVPN access CRUD; stats (`/traffic/by-day`, `/by-hour-port`, `/uptime`, `/sms-history`); `POST /pin-code`.
- **Rotation methods:** timer, dashboard button, action link, Telegram bot, or API `changeip`.

---

## 7. Mobile Proxy Space (mobileproxy.space) — VERIFIED

- **Site:** https://mobileproxy.space (a.k.a. SpaceProxy). Docs https://mobileproxy.space/api.html. Since 2020.
- **Proxy types:** Mobile 3G/4G/5G/LTE from real devices, ~40–52 countries, 170+ operators/cities. HTTP/HTTPS, SOCKS5. Period-based unlimited traffic, private dedicated channels.
- **Pricing (RUB primary):** "from 49₽"; ~490 RUB/day for private channels. Subscription, unlimited traffic. 2-hour free test.
- **Reputation:** One of the best-known RU/CIS mobile brands; large IP pool; popular for parsing/SMM/arbitrage.

### API CAPABILITIES (verified)
- **Base URL:** `https://mobileproxy.space/api.html` (command-style). IP-change host `https://changeip.mobileproxy.space/`.
- **Auth:** **Bearer** — `Authorization: Bearer {token}` (rotate link needs no auth).
- **SDKs:** official PHP/Node/Python on GitHub.
- **Commands:** `get_my_proxy`, `proxy_ip`, `get_price`, **`get_balance`**, **`buyproxy`** (purchase/renew), `edit_proxy`, `reboot_proxy`, `change_equipment`, `get_operators_list`, `get_id_country`/`get_id_city`/`get_geo_list`, blacklist commands (`get_black_list`, add/remove operator), `fingerprint_generate`, `tasks`, `see_the_url_from_different_IPs`.
- **IP rotation:** `GET https://changeip.mobileproxy.space/?proxy_key={key}&format=json` (no auth, not rate-limited).
- **Rate limits:** same request ≤1 per ~3–5s; general = 3 × active proxies per second; over → HTTP 429.

---

## 8. ASOCKS (asocks.com) — VERIFIED (Swagger)

- **Site:** https://asocks.com. Dashboard my.asocks.com. Company: IP Security LTD (BVI).
- **Proxy types:** Residential (rotating + sticky/static) and mobile. 7M+ IPs, 150–200 countries. HTTP/SOCKS5. Sticky ~15 min. Proxy auth: user/pass or IP whitelist.
- **Pricing (USD, PAYG):** $3/GB; 120GB=$360; ~1TB≈$3000; min deposit $15.
- **Reputation:** Popular with arbitrage/antidetect-browser users; ~80/20 positive. Complaints on referral payouts and some RU IP drops.

### API CAPABILITIES (verified)
- **Docs:** https://api.asocks.com/v2/swagger/docs (Swagger UI); FAQ https://faq.asocks.com/faq/article/how-to-use-api; in-account https://my.asocks.com/api-help; GitHub examples (PHP+Go) https://github.com/Asocks-proxy/API.
- **Base URL:** `https://api.asocks.com/v2/`.
- **Auth:** API key as **query param** `?apikey={KEY}` (also accepts `Authorization: Bearer`). Confirmed example: `GET /v2/plan/info?apikey=...`.
- **Capabilities (API replicates dashboard):** add balance, create ports, remove ports, fetch proxy address list, fetch locations/countries, plan/balance info. Can generate ports OR URL-links returning IP lists matching preset geo.
- **Confirmed endpoint:** `GET /v2/plan/info` (plan/balance). Exact paths for create-port / list / locations live in the Swagger UI — **pull the live OpenAPI JSON during the build** for authoritative paths/params.
- Promo `GITASOCKS` = 5GB free.

---

# Tier 2 — API exists but docs gated / confirm before coding

## 9. ProxyMarket (proxy.market)
- **Domain is `proxy.market`** (not proxy-market.ru); RU at ru.proxy.market. Since 2016.
- **Types:** Datacenter IPv4 (dedicated+shared), IPv6, **rotating datacenter** (traffic-billed), ISP, Residential, Mobile. 195 countries; pools: residential 22M, mobile 5M, ISP/dc 500k+, rotating dc 1.5M+. City-level geo.
- **Pricing (USD):** dc shared IPv4 from $0.09/IP; ISP $2.96/IP; residential $2.1/GB; mobile dedicated $15.34/IP; rotating dc $0.48/GB. $0.49 trial.
- **API:** Documented via **Swagger UI at https://api.dashboard.proxy.market/docs** (host `https://api.dashboard.proxy.market`). Supports **purchase, renew/prolong, retrieve proxy lists, create filtered lists (geo/type)**, traffic mgmt. Page is JS-rendered and `openapi.json` returned 405 to bots → **load in a browser / authenticated session to enumerate exact paths**; auth is API-token based.
- **Reputation:** Business-oriented multi-type provider; users praise the API. Rated ~4.7 in RU lists.

## 10. Proxys.io (proxys.io)
- Since 2016/2017. **Types:** IPv4 (server + residential-type, individual/shared), IPv6 (USA/Russia, limited rotation), Residential, Mobile (with city + carrier targeting). 80–240 countries claimed.
- **Pricing (USD):** individual server IPv4 ~$1.10–2.74/IP/mo; shared ~$0.67–0.80; IPv6 ~$0.14–0.27 (min 10); mobile ~$43–237/port. 50+ payment methods incl. crypto.
- **API:** **Personal API key** in dashboard ("Ключи API") used for script integration, a Telegram bot, and the "ProxyControl" browser extension. Mass TXT export for **static proxies only** (no mobile export). **No documented public REST endpoint catalog found** (proxys.io/api returned 503). Confirm exact endpoints/order-creation with support before coding. Likely follows the RU `getproxy`/`buy`/`prolong` family.
- **Reputation:** Top-tier RU brand (ecomservice.ru 4.8); clean IPs, fast RU support.

## 11. Froxy (froxy.com)
- Since ~2019. **Types:** Premium residential (10M+ IPs, 200+ locations), mobile, datacenter. HTTP/SOCKS5. Country/city/**ISP** targeting; rotation 90–3600s; up to 1000 ports. Trustpilot ~4.7–4.8.
- **Pricing (USD):** residential ~$6–8/GB entry scaling to ~$3000/mo for 1TB; ~7GB minimum.
- **API:** The practical surface is the **proxy gateway** `proxy.froxy.com:9000` with **user:pass in URL** and **geo encoded in the password string** (country `wifi;pt;;;`, city `wifi;us;;south+carolina;myrtle+beach`). A dashboard management API (subscriptions, export, locations) exists behind login with cURL/Py/Go/Node/PHP samples, but **no public REST endpoint reference/base URL/token scheme could be extracted** (JS-rendered marketing pages). Confirm management endpoints directly with Froxy.
- More global/Western-facing but available in CIS.

## 12. Proxy-Sale → Geonix (proxy-sale.com → geonix.com)
- **proxy-sale.com 301-redirects to https://geonix.com** ("Geonix, formerly Proxy-Sale"), part of the **Proxy-Seller family** and uses the **same `/personal/api/` platform / docs.proxy-seller.com**.
- **Types:** IPv4 (38 countries, from $0.50/IP), IPv6 (13, from $0.07/IP), ISP (24, from $1.35/IP), Mobile (17, from $14/IP), Residential (200+, from $0.70/GB).
- **API:** `https://proxy-seller.com/personal/api/v1/{ApiKey}/` — **key in URL path** — with `/balance/get`, `/order/calc`, `/order/make`, prolong, `/proxy/list/{type}` (`ipv4|ipv6|mobile|isp|mix|mix_isp|resident`), authorizations, residential lists/GEO. **Confirm whether Geonix exposes it under geonix.com or proxy-seller.com host for your key.** See Proxy-Seller section above for full endpoint table.

## 13. LTESocks (ltesocks.io)
- **Types:** Private ISP, IPv4, IPv6, Mobile 4G/5G/LTE on own hardware. SOCKS5/HTTPS. "Luminos AI" anti-block engine.
- **Pricing (USD):** custom/flexible; a review cited ~$3.5/GB; trial available.
- **API:** Repeatedly advertised (script integration, IP rotation, IP-pool mgmt, auto-delivery) but **the machine-readable reference (base URL, paths, auth) is gated behind the dashboard at my.ltesocks.io** — public pages describe capabilities only. Proxy auth = IP whitelist or user/pass; API key "in the dashboard." **Obtain the reference in-account or from support@ltesocks.io before building.**
- **Reputation:** Premium (fast 5G, low ping), pricier; positive Trustpilot/G2; heavy RU/CIS marketing.

---

# Tier 3 — no public API / avoid

## 14. AdvancedProxy (advanced.name)
- **Types:** HTTP(S)/SOCKS5 IPv4 + backconnect rotating; shared pools (World MIX, Europe, CIS/Russia, China). Large pools (50k+ IPs). Elite/anonymous, clean IPs, 60-min free trial.
- **Pricing:** USD (e.g. World MIX #2 = 12,000 proxies $378/mo); RU review cites ~100 RUB/hr. Flexible 1hr–1mo rental.
- **API:** **No public REST API found** — dashboard-only. Reputable in RU SEO/arbitrage circles but not a #1 name in 2026 listicles.

## 15. BeeProxy → 9Proxy (9proxy.com)
- beeproxy.com **301-redirects to 9proxy.com** (merged). Residential IPv4, all countries, HTTP/SOCKS5, sold via **CDkey/recharge codes** with "lifetime warranty." 20M+ IPs post-merger.
- **API:** **No public REST API documentation found** — client app + CDkey activation model. New (2025), less established in RU/CIS. Verify in-account if needed.

## 16. Local-IP — UNVERIFIED
- Could **not confirm** any proxy provider under this brand. `https://local-ip.space/` is unreachable (ECONNREFUSED); no search results, reviews, or RU listings. **The exact domain/brand needs re-confirmation** — possibly a different TLD, a very new service, or a slightly different name. No API details were fabricated.

## 17. RSocks (rsocks.net) — DEAD / DO NOT USE
- **Seized by FBI/US DOJ in June 2022** as a criminal botnet built on hacked devices; **still closed in 2025–2026.** Despite older RU reviews praising its API, **do not integrate.**

---

# Also surfaced in RU rankings (lighter detail)
- **GonzoProxy** — ranked #1 on ecomservice.ru 2026; residential from real devices, 190 countries.
- **CyberYozh** — mobile LTE/5G + residential, 100+ countries, **API**, RU rankings ~4.8.
- **Belurk** — cheap IPv6, **API**, ~4.5.
- **SX.ORG / Ake.net** — "proxy exchange" PAYG, 200–235 countries, **API**, top of uguide.ru (5.0).
- **NodeMaven** — residential/mobile, 150+ countries, 1400+ cities, API; popular for arbitrage.
- **PrivateProxy.me** — private datacenter + residential (rotating $1.50/GB at 1TB, static $5/IP/mo); endpoint-generator API + a separate **Reseller API** (register → activate key → white-label resell), but method-level docs are dashboard-gated. Western-leaning.
- **GetProxy.io, Floppydata** — recurring in RU lists, noted as **no API**.

---

# RU-market rankings summary (why leaders rank high)

**ecomservice.ru ("Рейтинг прокси-серверов в России 2026")** — filtered for RU bank-card support + good reviews:
1. Proxy6 (4.9, **API**) · 2. Proxys.io (4.8, **API**) · 3. CyberYozh (4.8, **API**) · 4. Proxy.Market (4.7, **API**) · 5. GetProxy.io (4.6, no API) · 6. Belurk (4.5, **API**) · 7. SX.ORG (4.4, **API**) · 8. Floppydata (4.4, no API).

**uguide.ru ("Рейтинг лучших прокси сервисов")** top tier: SX.ORG (5.0, API), Froxy (5.0), Asocks (5.0, RU pay), Proxy6.net, Fineproxy.org, Ake.net (API), SOCPROXY (mobile), Smartproxy. Strongest RU-domestic presence with ruble pricing: Proxy6.net, SOCPROXY, SpaceProxy/Mobile Proxy Space, Asocks.

**Common reasons leaders win:** acceptance of Russian bank cards / SBP, localized RU UI + ruble pricing, long track record (FineProxy 2011; Proxy6/Proxys.io/Proxy.Market/Proxy-Seller 2014–2016), broad geo coverage, and — increasingly a differentiator — a documented public API.

---

# Recommended implementation notes for the MCP server

1. **Templatize two transport adapters:** (a) key-in-URL-path (`{base}/api/{key}/{method}`) for Proxy6, Proxy-Store, Proxy-Seller; (b) header/param token for ProxyLine (`API-KEY`), iProxy & Mobile Proxy Space (Bearer), ASocks (`?apikey=`), FineProxy (Basic).
2. **Normalize a common tool surface** across providers: `list_proxies`, `buy_proxies`, `prolong_proxies`, `get_balance`, `list_countries`, `get_price/calc`, `check_proxy`, and for mobile `rotate_ip`. Proxy-Seller and ProxyLine need a **calc→make / price→order** two-step; Proxy6/Proxy-Store buy in one call.
3. **Map proxy "version/type" codes per provider** (Proxy6 3/4/5/6; Proxy-Seller `ipv4/ipv6/isp/mobile/mix/mix_isp/resident`).
4. **Respect rate limits:** Proxy6 3 req/s, ProxyLine 50 req/min, Mobile Proxy Space 3×active/s.
5. **Handle Proxy-Seller's HTTP-200-with-`errors[]`** convention separately from HTTP-status-based error handling (Proxy6 uses `error_id`).
6. **Rotation:** mobile providers expose a no-auth/Bearer **rotate link** (Mobile Proxy Space `changeip.mobileproxy.space`, iProxy action links/`changeip`) — treat as the simplest universal rotation primitive.
7. **Before coding Tier-2 providers** (ProxyMarket, Proxys.io, Froxy mgmt API, LTESocks), pull the live Swagger/in-dashboard reference for authoritative paths.

---

# Sources

**Proxy6:** https://proxy6.net/developers · https://px6.me/developers · https://proxy6.net/ · github.com/IvanMMM/proxy6 · github.com/vasilevIT/proxy6-api
**Proxy-Seller:** https://docs.proxy-seller.com · /proxy-seller/order-actions/place-an-order · /calculate-the-order · /actions-with-proxies/retrieve-active-proxy · /extend-proxies · /authorizations · /residential-proxy/api-tool · /api-changelog · https://proxy-seller.com/personal/api/ · github.com/proxy-seller (user-api-python/php/nodejs/java/golang) · pypi.org/project/proxy-seller-user-api
**ProxyLine:** https://proxyline.net/api · https://proxyline.net/ · https://panel.proxyline.net/api/
**Proxy-Store:** https://proxy-store.com/en/developers · https://proxy-store.com/
**FineProxy:** https://api.fineproxy.org/docs/ · https://fineproxy.org/ · https://fineproxy.org/prices/ · github.com/moriony/fine-proxy-client
**Proxys.io:** https://proxys.io/en · https://proxys.io/ru/residential · https://proxys.io/ru/blog/proksi-info/kak-ispolzovat-proksi-server-dlya-raboty-s-api
**Froxy:** https://froxy.com/en/api · https://help.froxy.com/en · https://scrapeops.io/proxy-providers/froxy/python-froxy-residential-proxy-guide/
**ProxyMarket:** https://proxy.market/ · https://api.dashboard.proxy.market/docs · https://ru.proxy.market/business
**Proxy-Sale/Geonix:** https://proxy-sale.com/ (→ https://geonix.com/) · https://docs.proxy-seller.com
**ASOCKS:** https://asocks.com/en/ · https://api.asocks.com/v2/swagger/docs · https://faq.asocks.com/faq/article/how-to-use-api · https://my.asocks.com/api-help · github.com/Asocks-proxy/API
**iProxy.online:** https://iproxy.online/ · https://iproxy.online/docs-api-connection · https://iproxy.online/pricing
**Mobile Proxy Space:** https://mobileproxy.space/en/ · https://mobileproxy.space/api.html · https://changeip.mobileproxy.space/
**LTESocks:** https://ltesocks.io/ · https://my.ltesocks.io/ · https://help.ltesocks.io/ · https://ltesocks.io/blog/using-apis-for-integration/
**AdvancedProxy:** https://advanced.name/ · https://advanced.name/price
**BeeProxy/9Proxy:** https://beeproxy.com (→ https://9proxy.com/) · https://www.scamadviser.com/check-website/beeproxy.com
**RSocks:** https://therecord.media/rsocks-botnet · https://en.wikipedia.org/wiki/Rsocks
**RU rankings:** https://ecomservice.ru/luchshie-proksi · https://uguide.ru/rejting-luchshie-proxy-servisy · https://vc.ru/luchshie/2728032-luchshie-proksi-servisy-2026-goda-top-15 · https://rateproxy.com/en/type/api/
