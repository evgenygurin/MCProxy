# MCProxy

**An [MCP](https://modelcontextprotocol.io) server that gives AI agents on-demand access to proxies from the world's leading and Russian/CIS proxy providers — through a single, unified interface.**

Built with [FastMCP 3](https://gofastmcp.com). When an agent needs a proxy, it calls one MCProxy tool; MCProxy talks to whichever provider you've configured and returns ready-to-use proxy strings.

> **Python 3.12 · FastMCP 3.4.2 · 11 implemented provider adapters · 14 more documented & planned · 11 unified tools**

---

## Why

Every proxy provider has its own API, auth scheme, and quirks. MCProxy normalizes them behind one provider-agnostic tool surface so an agent (or you) can:

- discover which providers are configured and what they support,
- **generate** or **list** proxies with geo-targeting and rotation,
- **buy** and **extend** proxies where the provider's API allows it,
- check **balance** / **usage** and list **targetable countries**,
- run requests through managed **scraping APIs**,

…without learning each vendor's API.

## How it works

```
AI agent ──MCP──> MCProxy (FastMCP server)
                      │
                      ├─ unified tools: list_providers, get_proxies,
                      │   generate_proxy_list, buy_proxies, check_balance, …
                      │
                      └─ provider registry ─> per-provider adapters ─HTTP─> vendor APIs
```

Each provider is a small adapter that maps the vendor's API onto shared models
(`ProxyEndpoint`, `BalanceInfo`, `CountryListResult`, …). A registry exposes them,
and a handful of generic tools dispatch to the right adapter based on a `provider`
argument. This keeps the tool count low (great for token usage) while supporting
many providers.

## Supported providers

### Implemented adapters

| Provider | Region | Types | Operations |
|---|---|---|---|
| **Webshare** | 🌍 US | datacenter, ISP, residential | list, balance, usage, countries |
| **IPRoyal** | 🌍 LT | residential | generate, balance, usage, countries |
| **ProxyMesh** | 🌍 US | datacenter, ISP | list, countries, usage |
| **ScraperAPI** | 🌍 US | scraping API | scrape, usage |
| **ScrapingBee** | 🌍 FR | scraping API | scrape, usage |
| **Proxy6** | 🇷🇺 RU | datacenter (IPv4/IPv6) | list, balance, countries, buy, extend |
| **ProxyLine** | 🇷🇺 RU | datacenter (IPv4/IPv6) | list, balance, countries, buy, extend |
| **Proxy-Store** | 🇷🇺 RU | datacenter, residential, mobile | list, balance, countries, buy, extend |
| **Proxy-Seller** | 🇷🇺 RU | IPv4/IPv6/ISP/mobile/residential | list, balance, countries |
| **ASOCKS** | 🇷🇺 RU/CIS | residential, mobile | balance |
| **FineProxy** | 🇷🇺 RU | datacenter, ISP, residential | balance |

### Documented & planned

`list_providers` also surfaces a catalog of major providers with public APIs whose
adapters are planned: **Bright Data, Oxylabs, Decodo (Smartproxy), SOAX, NetNut,
Infatica, Proxy-Cheap, Zyte, Nimble, Rayobyte** (global) and **Mobile Proxy Space,
iProxy.online, ProxyMarket, Froxy** (RU/CIS). See
[`docs/PROVIDERS.md`](docs/PROVIDERS.md) for the full landscape, API notes and sources.

## Install

Requires **Python 3.12+**. [`uv`](https://docs.astral.sh/uv/) recommended.

```bash
git clone https://github.com/evgenygurin/mcproxy.git
cd mcproxy
uv venv --python 3.12
uv pip install -e .            # add ".[dev]" for tests/linting
```

## Configure

Credentials are read from environment variables (or a local `.env`). Configure only
the providers you use. Copy [`.env.example`](.env.example) and fill in your keys:

```bash
cp .env.example .env
# e.g.
WEBSHARE_API_KEY=...
IPROYAL_API_TOKEN=...
PROXY6_API_KEY=...
```

`list_providers` shows which providers are `configured` and the exact env var names
each one needs.

## Run

```bash
# stdio (default — for Claude Desktop, Cursor, etc.)
uv run mcproxy
# or
uv run fastmcp run server.py:mcp

# HTTP transport
MCPROXY_TRANSPORT=http MCPROXY_PORT=8000 uv run mcproxy
```

### Use with an MCP client

```json
{
  "mcpServers": {
    "mcproxy": {
      "command": "uv",
      "args": ["run", "mcproxy"],
      "env": {
        "WEBSHARE_API_KEY": "your-key",
        "PROXY6_API_KEY": "your-key"
      }
    }
  }
}
```

## Tools

| Tool | Purpose |
|---|---|
| `list_providers` | Discover providers, capabilities and config status. **Start here.** |
| `get_provider_info` | Capabilities for one provider. |
| `get_proxies` | List proxies already on your account (fixed-IP providers). |
| `generate_proxy_list` | Generate proxy strings with geo + rotation (residential pools). |
| `buy_proxies` | Purchase new proxies (spends money; supported providers only). |
| `extend_proxies` | Renew existing proxies by ID. |
| `check_balance` / `get_usage` | Monitor spend and traffic. |
| `list_countries` | Targetable locations for a provider. |
| `scrape` | Fetch a URL through a managed scraping API. |
| `acquire_proxy` | "Just give me a proxy" — picks a configured provider automatically. |

Every returned proxy includes a ready-to-use `url` (e.g. `http://user:pass@host:port`).

## Settings

Global options use the `MCPROXY_` prefix:

| Variable | Default | Description |
|---|---|---|
| `MCPROXY_TRANSPORT` | `stdio` | `stdio`, `http`, or `sse`. |
| `MCPROXY_HOST` / `MCPROXY_PORT` | `127.0.0.1` / `8000` | HTTP bind address. |
| `MCPROXY_REQUEST_TIMEOUT` | `30` | Outbound HTTP timeout (seconds). |
| `MCPROXY_DEFAULT_PROVIDER` | – | Preferred provider for `acquire_proxy`. |

## Project layout

```
src/mcproxy/
├── server.py          # FastMCP server + the unified tools
├── models.py          # shared provider-agnostic models
├── config.py          # settings + env credential loading
├── http.py            # async httpx helpers (build_client, as_float, …)
└── providers/
    ├── __init__.py    # Registry + IMPLEMENTED list
    ├── base.py        # BaseProvider contract
    ├── catalog.py     # documented-but-planned providers
    └── <provider>.py  # one adapter per provider
server.py              # root entrypoint for `fastmcp run server.py:mcp`
tests/                 # in-memory MCP client + mocked HTTP (respx)
docs/                  # PROVIDERS.md + research/
```

## Development

```bash
uv pip install -e ".[dev]"
uv run pytest          # tests (in-memory MCP client + mocked HTTP)
uv run ruff check .    # lint
uv run mypy src        # types
```

Adding a provider: create `src/mcproxy/providers/<name>.py` subclassing
`BaseProvider`, override the operations it supports, and register it in
`src/mcproxy/providers/__init__.py`. See `webshare.py` (header-token auth) and
`proxy6.py` (key-in-URL auth) as references, and
[`CLAUDE.md`](CLAUDE.md) / [`docs/PROVIDERS.md`](docs/PROVIDERS.md) for the
conventions and the full provider landscape.

## Disclaimer

Use proxies lawfully and in accordance with each provider's terms of service and
applicable law. This project is an integration layer; it does not endorse misuse.

## License

[MIT](LICENSE)
