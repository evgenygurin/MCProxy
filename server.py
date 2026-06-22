"""Root entrypoint so the server can be loaded by file path.

This lets you run the server with the FastMCP CLI:

    fastmcp run server.py:mcp --transport http

It simply re-exports the assembled server from the installed package (the actual
implementation lives in ``src/mcproxy/server.py``).
"""

from mcproxy.server import mcp

__all__ = ["mcp"]

if __name__ == "__main__":
    mcp.run()
