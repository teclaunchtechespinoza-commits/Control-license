import os, pytest, pymongo
ROTA_NOTIF = "/notifications"  # POST que cria/enfileira notificação

@pytest.mark.asyncio
async def test_notifications_idempotent(client, tenant_id, idem_key):
    payload = {"license_id": "LIC-001", "type": "expiration", "channel": "whatsapp"}

    r1 = await client.post(
        ROTA_NOTIF,
        json=payload,
        headers={"X-Tenant-ID": tenant_id, "Idempotency-Key": idem_key, "Content-Type": "application/json"},
    )
    assert r1.status_code in (200, 201), r1.text

    r2 = await client.post(
        ROTA_NOTIF,
        json=payload,
        headers={"X-Tenant-ID": tenant_id, "Idempotency-Key": idem_key, "Content-Type": "application/json"},
    )
    assert r2.status_code in (200, 201), r2.text

    uri = os.environ["MONGODB_URI"]
    cli = pymongo.MongoClient(uri)
    pref = os.environ.get("TENANT_DB_PREFIX", "licenser_")
    db = cli[pref + tenant_id]

    notif_count = db.notifications.count_documents({
        "tenant_id": tenant_id,
        "license_id": payload["license_id"],
        "type": payload["type"],
        "channel": payload["channel"],
    })
    assert notif_count == 1, f"Esperado 1 notificação, encontrado {notif_count}"
