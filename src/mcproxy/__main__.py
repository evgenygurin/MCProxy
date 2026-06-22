"""Entry point: ``python -m mcproxy`` or the ``mcproxy`` console script."""

from __future__ import annotations

from .config import get_settings
from .server import mcp


def main() -> None:
    settings = get_settings()
    transport = settings.transport.lower()
    if transport in ("http", "streamable-http", "sse"):
        mcp.run(transport=transport, host=settings.host, port=settings.port)  # type: ignore[arg-type]
    else:
        mcp.run()  # stdio (default)


if __name__ == "__main__":
    main()
