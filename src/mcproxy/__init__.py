"""MCProxy — a FastMCP server for on-demand proxy access across many providers."""

from __future__ import annotations

__version__ = "0.1.0"

from .server import build_server, mcp

__all__ = ["__version__", "build_server", "mcp"]
