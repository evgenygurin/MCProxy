from __future__ import annotations

import pytest
from fastmcp import Client

from mcproxy.server import build_server


@pytest.fixture
def server():
    return build_server()


@pytest.fixture
def client(server):
    return Client(server)
