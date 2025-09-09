import os, asyncio, uuid
import pymongo
import pytest
from httpx import AsyncClient
from asgi_lifespan import LifespanManager

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017/licenser_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SEED_DEMO", "false")
os.environ.setdefault("JWT_SECRET", "test-secret-please-change")
os.environ.setdefault("JWT_ALG", "HS256")
os.environ.setdefault("TZ", "America/Recife")
os.environ.setdefault("TENANT_DB_PREFIX", "licenser_")

from backend.server import app

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def mongo_client():
    uri = os.environ["MONGODB_URI"]
    cli = pymongo.MongoClient(uri)
    yield cli
    dbname = pymongo.uri_parser.parse_uri(uri)["database"]
    cli.drop_database(dbname)
    cli.close()

@pytest.fixture
async def client():
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            yield ac

@pytest.fixture
def tenant_id():
    return "tenant-test"

@pytest.fixture
def idem_key():
    return str(uuid.uuid4())

def _db(cli, tenant):
    pref = os.environ.get("TENANT_DB_PREFIX", "licenser_")
    return cli[pref + tenant]

@pytest.fixture(autouse=True)
def clean_tenant_db(mongo_client, tenant_id):
    d = _db(mongo_client, tenant_id)
    for c in ["licenses", "notifications", "notification_queue", "users", "events"]:
        try:
            d[c].delete_many({})
        except Exception:
            pass
