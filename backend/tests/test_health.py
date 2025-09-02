import time, pytest

@pytest.mark.asyncio
async def test_health_fast_response(client):
    t0 = time.perf_counter()
    r = await client.get("/health")
    t1 = time.perf_counter()
    assert r.status_code == 200
    assert (t1 - t0) < 0.5, f"Health demorou {(t1-t0):.3f}s"
