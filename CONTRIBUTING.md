# Contributing to MCProxy

Thanks for your interest in improving MCProxy! New **provider adapters** are the
most valuable contribution, but bug fixes, docs, and tests are equally welcome.

By participating you agree to keep things respectful and constructive, and that
your contributions are licensed under the project's [MIT License](LICENSE).

## Getting started

Requires **Python 3.12+**. [`uv`](https://docs.astral.sh/uv/) is recommended.

```bash
git clone https://github.com/evgenygurin/mcproxy.git
cd mcproxy
uv venv --python 3.12
uv pip install -e ".[dev]"   # runtime + pytest, ruff, mypy, respx
```

No credentials are needed for development — the test suite uses an in-memory MCP
client and mocks all outbound HTTP.

## Quality gate

Run all three before opening a PR; CI/maintainers expect them green:

```bash
uv run ruff check .    # lint   (config in pyproject.toml)
uv run mypy src        # types
uv run pytest          # tests
```

- `ruff` intentionally ignores `E501` (long lines) and `RUF012` (adapters use
  mutable class-level attributes as declarative config). Keep everything else clean.
- Tests use `asyncio_mode = "auto"`, so `async def test_*` needs no decorator.
- Run a single test with, e.g.,
  `uv run pytest tests/test_providers.py::test_webshare_list_proxies`.

## Adding a provider

Adapters live in `src/mcproxy/providers/`. Each one subclasses `BaseProvider`
(`base.py`), maps a vendor's API onto the shared models in `models.py`, and
overrides only the operations it actually supports. `webshare.py` (header-token
auth) and `proxy6.py` (key-in-URL auth) are good references.

1. **Create** `src/mcproxy/providers/<name>.py` subclassing `BaseProvider`. Set the
   class attributes: `name`, `display_name`, `website`, `country_of_origin`,
   `proxy_types`, `operations`, `credential_env`, `notes`.
2. **Implement** only the operation methods you list in `operations` — this list
   is the provider's public contract, surfaced by `list_providers`. Unimplemented
   operations inherit `BaseProvider`'s `OperationNotSupported`. Return the shared
   models (`ProxyListResult`, `BalanceInfo`, `CountryListResult`, …).
3. **HTTP & credentials:** use `self.client(...)` (from `http.py`) and
   `json_or_raise()`; read secrets via `self.require_credential()` and declare the
   env var names in `credential_env`. Credentials come **only** from env vars —
   never as tool arguments.
4. **Parse defensively.** `_dispatch` in `server.py` only translates
   `ProviderError` / `ProviderNotConfigured` / `httpx.HTTPError` into clean tool
   errors. Any other exception (`KeyError`, `ValueError`, `IndexError`, …) escapes
   as an unhandled 500 — so guard missing keys, coerce numbers via `http.as_float`,
   and raise `ProviderError` on unexpected response shapes.
5. **Register** the class in `IMPLEMENTED` in `providers/__init__.py` (and remove
   it from `catalog.py` if it was listed as planned).
6. **Document & test:** add the env vars to [`.env.example`](.env.example) and a
   respx-mocked test in `tests/test_providers.py`.

See [`CLAUDE.md`](CLAUDE.md) for the architecture in depth and
[`docs/PROVIDERS.md`](docs/PROVIDERS.md) for the full provider landscape and API
notes.

## Pull requests

- Branch off `main`; keep each PR focused on one logical change.
- Write a clear description of **what** changed and **why**.
- Make sure the quality gate passes and add tests for new behavior.
- Link any related issue. For larger changes, open an
  [issue](https://github.com/evgenygurin/mcproxy/issues) first so we can align on
  direction before you invest time.

## Reporting bugs & requesting features

Open a [GitHub issue](https://github.com/evgenygurin/mcproxy/issues). For bugs,
include the provider involved, the tool call, what you expected, what happened,
and any error message (with credentials redacted).
