# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

MCProxy is a **FastMCP 3** server (Python 3.12) that gives AI agents on-demand
access to proxies from many providers (global + Russian/CIS) through one
**provider-agnostic** tool surface. An agent calls a single tool with a
`provider` argument; the server dispatches to that provider's adapter and returns
a normalized result.

## Commands

```bash
# Setup (uv; venv is git-ignored)
uv venv --python 3.12
uv pip install -e ".[dev]"

# Quality gate (run all three before committing)
uv run ruff check .          # lint  (ruff config in pyproject.toml)
uv run mypy src              # types (strict-ish; keep this clean)
uv run pytest -q             # tests

# A single test
uv run pytest tests/test_providers.py::test_proxy6_check_balance -q

# Run the server
uv run mcproxy                                   # stdio (default)
MCPROXY_TRANSPORT=http uv run mcproxy            # HTTP transport
uv run fastmcp run server.py:mcp                 # via FastMCP CLI
uv run fastmcp inspect server.py:mcp             # list tools / sanity check
```

Tests use the FastMCP **in-memory client** (`Client(server)`) and **respx** to
mock outbound HTTP — they never hit real provider APIs and need no credentials.
`asyncio_mode = "auto"`, so `async def test_*` needs no decorator.

## Architecture

The deliberate design choice is **few unified tools over a registry of adapters**,
not one tool per provider (keeps the tool count + token usage low). Three layers:

1. **Tools** (`src/mcproxy/server.py`) — `build_server()` defines ~11 generic
   tools (`list_providers`, `get_proxies`, `generate_proxy_list`, `buy_proxies`,
   `extend_proxies`, `check_balance`, `get_usage`, `list_countries`, `scrape`,
   `acquire_proxy`, `get_provider_info`). Each takes a `provider: str`, looks it
   up in the registry, and `await`s the adapter method wrapped in `_dispatch(...)`.
2. **Registry** (`src/mcproxy/providers/__init__.py`) — `Registry` instantiates
   every class in `IMPLEMENTED` and resolves them by `name`. `capabilities()`
   merges implemented adapters with `catalog.planned_catalog()` (documented but
   unimplemented providers) so `list_providers` shows the whole landscape.
3. **Adapters** (`src/mcproxy/providers/<name>.py`) — each subclasses
   `BaseProvider`, maps one vendor's API onto the shared models, and overrides
   only the operations it supports.

Supporting modules: `models.py` (shared Pydantic models + the `ProxyType` /
`Operation` / `Rotation` / `ProxyProtocol` enums), `config.py` (settings +
credential loading), `http.py` (httpx client factory + helpers).

### Key invariants — keep these true when changing code

- **`operations` must match overridden methods.** An adapter's `operations`
  list is its public contract (surfaced by `list_providers`). `BaseProvider`'s
  default methods raise `OperationNotSupported`; only declare an `Operation` you
  actually override, and don't override one you don't declare.
- **Errors must be `ProviderError`/`ProviderNotConfigured`/`httpx.HTTPError`.**
  `_dispatch` in `server.py` only translates those (plus `ToolError`) into clean
  tool errors. Any other exception (KeyError, ValueError, IndexError, TypeError)
  escapes as an unhandled 500 — so parse provider responses defensively
  (guard missing keys, non-numeric values via `http.as_float`, empty lists,
  non-list JSON) and raise `ProviderError` on unexpected shapes.
- **Credentials are read live, settings are cached.** `config.get_credential()`
  reads `os.environ` on every call (so tests can `monkeypatch.setenv` after the
  registry is built); only `get_settings()` (global `MCPROXY_*` options) is
  `lru_cache`d. Per-provider keys are never cached.
- **Credentials come only from env**, named in each adapter's `credential_env`
  and documented in `.env.example`. Tools never accept credentials as arguments.
- **`server.py` (repo root) is a thin re-export** of `mcproxy.server.mcp` so the
  FastMCP CLI can load the server by file path — the package uses relative
  imports, which break when a module under `src/` is loaded directly.

### Adding a provider

1. Create `src/mcproxy/providers/<name>.py` subclassing `BaseProvider`; set the
   class attributes (`name`, `display_name`, `website`, `country_of_origin`,
   `proxy_types`, `operations`, `credential_env`, `notes`) and override the
   supported operation methods, returning the shared models.
2. Add the class to `IMPLEMENTED` in `providers/__init__.py` (and remove it from
   `catalog.py` if it was listed as planned).
3. Add its env vars to `.env.example` and a respx-mocked test in
   `tests/test_providers.py`.

Reference adapters: `webshare.py` (header-token auth, REST), `proxy6.py`
(key-in-URL-path auth), `proxymesh.py` (HTTP Basic), `scraperapi.py`
(scraping API). Auth patterns are summarized in `docs/PROVIDERS.md`.

## Conventions

- Python 3.12 features are fine (e.g. PEP 695 generics, `StrEnum`).
- `ruff` ignores `RUF012` (adapters use mutable class-level attributes as
  declarative config) and `E501`; otherwise keep lint + mypy clean.
- Excluded by design (do not add): GeoSurf (defunct), Storm Proxies (no API),
  RSocks (seized). See `docs/research/` for the sourcing behind every provider.
