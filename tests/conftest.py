import subprocess
import sys
import time

import httpx
import pytest
from httpx import AsyncClient, ASGITransport

_CLIPBOARD_INIT_SCRIPT = """
(function () {
    try {
        var desc = Object.getOwnPropertyDescriptor(Navigator.prototype, 'clipboard');
        var val = desc && desc.get ? desc.get.call(navigator) : navigator.clipboard;
        Object.defineProperty(navigator, 'clipboard', {
            configurable: true,
            get: function () { return val; },
            set: function (v) { val = v; },
        });
    } catch (_) {}
})();
"""


def pytest_collection_modifyitems(items):
    for item in items:
        if "test_frontend" in item.fspath.basename:
            item.add_marker(pytest.mark.frontend)


@pytest.fixture(autouse=True)
def _maak_clipboard_schrijfbaar(request):
    """Maak navigator.clipboard schrijfbaar zodat frontend-tests hem kunnen mocken."""
    if "test_frontend" not in str(request.node.fspath):
        return
    try:
        context = request.getfixturevalue("context")
    except pytest.FixtureLookupError:
        return
    context.add_init_script(_CLIPBOARD_INIT_SCRIPT)

BASE_URL = "http://localhost:3000"
_server_process = None


def _server_is_running() -> bool:
    try:
        httpx.get(f"{BASE_URL}/api/sessions", timeout=2.0)
        return True
    except Exception:
        return False


def _wait_for_server(timeout: int = 15) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _server_is_running():
            return
        time.sleep(0.5)
    raise RuntimeError(f"Server niet bereikbaar op {BASE_URL} na {timeout} seconden.")


@pytest.fixture(scope="session", autouse=True)
def server():
    """Start de server als die nog niet draait. Stopt hem na de sessie als wij hem gestart hebben."""
    global _server_process

    if _server_is_running():
        yield
        return

    _server_process = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_server()
        yield
    finally:
        _server_process.terminate()
        _server_process.wait()
        _server_process = None


@pytest.fixture
async def client():
    from app import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def live_client():
    """Echte HTTP-client die via het netwerk communiceert met de draaiende server."""
    async with AsyncClient(base_url=BASE_URL, timeout=15.0) as c:
        yield c
