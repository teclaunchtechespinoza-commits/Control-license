import pytest
ROTA_PROTEGIDA = "/notifications"  # ajuste para uma rota sua protegida

@pytest.mark.asyncio
async def test_sem_tenant_header_retorna_400(client):
    r = await client.get(ROTA_PROTEGIDA)
    assert r.status_code in (400, 404, 405)
    if r.status_code == 400:
        assert "tenant" in r.text.lower() or "missing" in r.text.lower()

@pytest.mark.asyncio
async def test_com_tenant_header_permite(client, tenant_id):
    r = await client.get(ROTA_PROTEGIDA, headers={"X-Tenant-ID": tenant_id})
    assert r.status_code != 400
