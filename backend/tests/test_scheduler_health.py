import pytest

@pytest.mark.asyncio
async def test_scheduler_health_endpoint(client, tenant_id):
    r = await client.get("/scheduler/health", headers={"X-Tenant-ID": tenant_id})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "job_count" in data and "running" in data
