import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def client():
    from app import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
