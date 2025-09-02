async def ensure_indexes(db):
    await db.licenses.create_index([("serial", 1)], unique=True, name="uniq_serial")
    await db.notifications.create_index(
        [("license_id", 1), ("type", 1), ("channel", 1)],
        unique=True, name="uniq_license_type_channel"
    )
    await db.notification_queue.create_index(
        [("notification_id", 1)],
        unique=True, name="uniq_notification_in_queue"
    )
    # TTL opcional para eventos (se a coleção existir)
    try:
        cols = await db.list_collection_names()
        if "events" in cols:
            await db.events.create_index([("createdAt", 1)], expireAfterSeconds=60*60*24*30)
    except Exception:
        pass
