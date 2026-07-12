import os
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

TEST_PORT = 3001
BASE_URL = f"http://localhost:{TEST_PORT}"
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


def _find_listening_pid(port: int) -> int | None:
    result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[0] == "TCP" and parts[-2] == "LISTENING":
            local_addr = parts[1]
            if local_addr.endswith(f":{port}"):
                return int(parts[-1])
    return None


def _process_image_name(pid: int) -> str | None:
    result = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
        capture_output=True,
        text=True,
    )
    line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
    if not line.startswith('"'):
        return None
    return line.split('","')[0].strip('"')


def _kill_stale_server(port: int = TEST_PORT, timeout: int = 5) -> None:
    """Beëindig een verweesd proces op deze poort, zodat tests nooit tegen oude code draaien."""
    pid = _find_listening_pid(port)
    if pid is None:
        return

    image_name = _process_image_name(pid)
    if image_name is not None and image_name.lower() != "python.exe":
        raise RuntimeError(
            f"Poort {port} is in gebruik door proces {pid} ({image_name}), geen "
            "python.exe — wordt niet automatisch gestopt."
        )

    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _find_listening_pid(port) is None:
            return
        time.sleep(0.2)

    raise RuntimeError(
        f"Kon proces {pid} op poort {port} niet stoppen binnen {timeout} seconden."
    )


@pytest.fixture(scope="session", autouse=True)
def server():
    """Start altijd een verse server-instantie op de testpoort (los van een eventuele
    handmatig gestarte app op de standaardpoort). Beëindigt eerst een achtergebleven
    proces op de testpoort."""
    global _server_process

    _kill_stale_server()

    env = os.environ.copy()
    env["PORT"] = str(TEST_PORT)
    _server_process = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
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
