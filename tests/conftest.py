import pytest
import httpx
from httpx import AsyncClient, ASGITransport

LIVE_BASE_URL = "http://localhost:3000"


@pytest.fixture
async def client():
    from app import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def live_client():
    """Echte HTTP-client die via het netwerk communiceert met de draaiende server."""
    async with AsyncClient(base_url=LIVE_BASE_URL, timeout=15.0) as c:
        try:
            await c.get("/api/sessions")
        except httpx.ConnectError:
            pytest.skip(f"Server niet bereikbaar op {LIVE_BASE_URL} — start de app eerst")
        yield c
