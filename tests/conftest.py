import socket

import pytest


@pytest.fixture
def listening_port():
    """A port with a real listener on it. The OS picks a free one (port 0)."""
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        yield server.getsockname()[1]


@pytest.fixture
def unused_port():
    """A port that was free a moment ago and has nothing listening on it."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    return port
