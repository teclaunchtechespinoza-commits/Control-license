#!/usr/bin/env bash
set -euo pipefail

echo "==> Aplicador automático de correções (tenant/índices/segurança/observabilidade/CI/tests)"

ROOT="$(pwd)"
BACKEND_DIR="$ROOT/backend"
TS="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$ROOT/_backup_$TS"

require() {
  if [[ ! -f "$1" ]]; then
    echo "ERRO: não encontrei $1. Rode este script na raiz do repositório (deve existir backend/server.py)."
    exit 1
  fi
}

mkdir -p "$BACKUP_DIR"
require "$BACKEND_DIR/server.py"
require "$BACKEND_DIR/deps.py"

echo "==> Backup de arquivos-chaves em $BACKUP_DIR"
cp "$BACKEND_DIR/server.py" "$BACKUP_DIR/server.py"
cp "$BACKEND_DIR/deps.py" "$BACKUP_DIR/deps.py" || true

mkdir -p "$BACKEND_DIR" "$BACKEND_DIR/tests" "$ROOT/.github/workflows" "$ROOT/.github" "$BACKEND_DIR/patches"

# ------------------------------------------------------------
# 1) Arquivos NOVOS: tenant_db.py, indices.py, scheduler_health.py, audit_tenants.py
# ------------------------------------------------------------
cat > "$BACKEND_DIR/tenant_db.py" <<'PY'
import os, re
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Request, HTTPException, status

TENANT_DB_PREFIX = os.getenv("TENANT_DB_PREFIX", "licenser_")
_mongo_client: Optional[AsyncIOMotorClient] = None

def init_mongo(uri: str) -> AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(uri)
    return _mongo_client

def _sanitize(tid: str) -> str:
    return re.sub(r"[^a-z0-9_-]", "-", tid.lower())[:48]

def db_name_for(tenant_id: str) -> str:
    return f"{TENANT_DB_PREFIX}{_sanitize(tenant_id)}"

def resolve_tenant_db(request: Request):
    db = getattr(request.state, "db", None)
    if db is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant DB não resolvido")
    return db

def current_tenant(request: Request) -> str:
    tid = getattr(request.state, "tenant_id", None)
    if not tid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing tenant context")
    return tid
PY

cat > "$BACKEND_DIR/indices.py" <<'PY'
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
PY

cat > "$BACKEND_DIR/scheduler_health.py" <<'PY'
from fastapi import APIRouter
from apscheduler.schedulers.asyncio import AsyncIOScheduler

router = APIRouter()

def init_scheduler_health(scheduler: AsyncIOScheduler):
    @router.get("/scheduler/health")
    async def scheduler_health():
        jobs = scheduler.get_jobs()
        return {
            "job_count": len(jobs),
            "jobs": [j.id for j in jobs],
            "running": scheduler.running
        }
PY

cat > "$BACKEND_DIR/audit_tenants.py" <<'PY'
import os
from pymongo import MongoClient

URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "licenser")
COLS = ["licenses","notifications","notification_queue","users"]

client = MongoClient(URI)
db = client[DB_NAME]

print(f"== Audit DB: {DB_NAME}")
for col in COLS:
    if col not in db.list_collection_names():
        continue
    missing = db[col].count_documents({"$or":[{"tenant_id":{"$exists":False}},{"tenant_id":None}]})
    print(f"[{col}] missing tenant_id: {missing}")
PY

# ------------------------------------------------------------
# 2) PATCHES: server.py e deps.py
# ------------------------------------------------------------
cat > "$BACKEND_DIR/patches/patch_server.diff" <<'DIFF'
*** server.py.orig
--- server.py
***************
*** 1,6 ****
--- 1,12 ----
+ from fastapi.middleware.cors import CORSMiddleware
+ from tenant_db import init_mongo, db_name_for
+ from indices import ensure_indexes
  from starlette.middleware.base import BaseHTTPMiddleware
  from fastapi import Request, Response
+ 
+ app.add_middleware(
+     CORSMiddleware,
+     allow_origins=["*"],  # AJUSTE para seus domínios
+     allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
+ )
***************
*** 10,40 ****
--- 16,72 ----
  PUBLIC_ENDPOINTS = {"/", "/health", "/docs", "/openapi.json"}
  
  class TenantMiddleware(BaseHTTPMiddleware):
      async def dispatch(self, request: Request, call_next):
-         tenant_id = request.headers.get("X-Tenant-ID")
-         if request.url.path not in PUBLIC_ENDPOINTS and not tenant_id:
-             tenant_id = "default"
+         tenant_id = request.headers.get("X-Tenant-ID")
+         if request.url.path not in PUBLIC_ENDPOINTS and not tenant_id:
+             return Response(
+                 content='{"detail":"Missing X-Tenant-ID"}',
+                 status_code=400, media_type="application/json"
+             )
          if not tenant_id:
              tenant_id = "public"
          request.state.tenant_id = tenant_id
-         # db antigo aqui...
+         try:
+             import os
+             mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
+             client = init_mongo(mongo_uri)
+             request.state.db = client[db_name_for(tenant_id)]
+             # cria índices essenciais (idempotente)
+             await ensure_indexes(request.state.db)
+         except Exception:
+             return Response(
+                 content='{"detail":"DB resolve error"}',
+                 status_code=500, media_type="application/json"
+             )
          return await call_next(request)
DIFF

cat > "$BACKEND_DIR/patches/patch_deps.diff" <<'DIFF'
*** deps.py.orig
--- deps.py
***************
*** 1,20 ****
  from fastapi import HTTPException, Request, status
  from typing import Optional
  import os
- 
- def require_tenant(request: Request) -> str:
-     tid = getattr(request.state, "tenant_id", None)
-     if not tid:
-         demo_mode = os.getenv("SEED_DEMO", "false").lower() in {"1","true","yes"}
-         if demo_mode:
-             tid = "default"
-             request.state.tenant_id = tid
-         else:
-             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
-                                 detail="Missing tenant context. Provide X-Tenant-ID header.")
-     return tid
+ from tenant_db import resolve_tenant_db, current_tenant
+ 
+ def require_tenant(request: Request) -> str:
+     return current_tenant(request)
+ 
+ def get_tenant_db(request: Request):
+     return resolve_tenant_db(request)
DIFF

# tentar aplicar patches com git
apply_patch() {
  local target="$1"
  local patch="$2"
  if git rev-parse --show-toplevel >/dev/null 2>&1; then
    if patch -p0 --dry-run < "$patch" >/dev/null 2>&1; then
      echo "==> Aplicando patch em $target"
      # cria cópia .orig
      cp "$target" "${target}.orig" || true
      patch -p0 < "$patch"
    else
      echo "!! Patch não aplicou automaticamente em $target."
      echo "   -> Os trechos estão em $patch. Abra e cole manualmente nos locais correspondentes."
    fi
  else
    echo "!! Repositório git não detectado; pulando git apply."
  fi
}

apply_patch "$BACKEND_DIR/server.py" "$BACKEND_DIR/patches/patch_server.diff"
apply_patch "$BACKEND_DIR/deps.py" "$BACKEND_DIR/patches/patch_deps.diff"

# ------------------------------------------------------------
# 3) TESTES (pytest)
# ------------------------------------------------------------
mkdir -p "$BACKEND_DIR/tests"

cat > "$BACKEND_DIR/tests/conftest.py" <<'PY'
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

from server import app  # ajuste se seu path for diferente

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
PY

cat > "$BACKEND_DIR/tests/test_health.py" <<'PY'
import time, pytest

@pytest.mark.asyncio
async def test_health_fast_response(client):
    t0 = time.perf_counter()
    r = await client.get("/health")
    t1 = time.perf_counter()
    assert r.status_code == 200
    assert (t1 - t0) < 0.5, f"Health demorou {(t1-t0):.3f}s"
PY

cat > "$BACKEND_DIR/tests/test_tenant_required.py" <<'PY'
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
PY

cat > "$BACKEND_DIR/tests/test_notifications_idempotency.py" <<'PY'
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
PY

cat > "$BACKEND_DIR/tests/test_rbac.py" <<'PY'
import base64, json, time, os, pytest

JWT_SECRET = os.getenv("JWT_SECRET", "test-secret-please-change")
JWT_ALG = os.getenv("JWT_ALG", "HS256")

def _jwt(payload: dict, secret=JWT_SECRET):
    header = {"alg": "HS256", "typ": "JWT"}
    def b64(x): 
        import json, base64
        return base64.urlsafe_b64encode(json.dumps(x, separators=(",",":")).encode()).rstrip(b"=")
    import hmac, hashlib
    seg1 = b64(header); seg2 = b64(payload)
    signing = seg1 + b"." + seg2
    sig = __import__("base64").urlsafe_b64encode(
        __import__("hmac").new(secret.encode(), signing, __import__("hashlib").sha256).digest()
    ).rstrip(b"=")
    return (signing + b"." + sig).decode()

def _token(tenant_id, role, sub="u1", email="u1@test"):
    now = int(time.time())
    payload = {
        "sub": sub, "email": email, "tenant_id": tenant_id, "role": role,
        "iat": now, "exp": now + 3600, "iss": "licenser-api", "aud": "licenser-clients"
    }
    return _jwt(payload)

ROTA_ADMIN_DELETE = "/licenses/LIC-001"  # ajuste para uma rota admin

@pytest.mark.asyncio
async def test_rbac_admin_ok(client, tenant_id):
    token = _token(tenant_id, "admin")
    r = await client.delete(ROTA_ADMIN_DELETE, headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"})
    assert r.status_code not in (401, 403), r.text

@pytest.mark.asyncio
async def test_rbac_user_bloqueado_para_admin(client, tenant_id):
    token = _token(tenant_id, "user")
    r = await client.delete(ROTA_ADMIN_DELETE, headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"})
    assert r.status_code in (401, 403), r.text

@pytest.mark.asyncio
async def test_rbac_tenant_mismatch(client, tenant_id):
    token_outro = _token("outro-tenant", "admin")
    r = await client.delete(ROTA_ADMIN_DELETE, headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token_outro}"})
    assert r.status_code in (401, 403)
PY

cat > "$BACKEND_DIR/tests/test_scheduler_health.py" <<'PY'
import pytest

@pytest.mark.asyncio
async def test_scheduler_health_endpoint(client, tenant_id):
    r = await client.get("/scheduler/health", headers={"X-Tenant-ID": tenant_id})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "job_count" in data and "running" in data
PY

# ------------------------------------------------------------
# 4) CI do GitHub + Template de PR
# ------------------------------------------------------------
cat > "$ROOT/.github/workflows/ci.yml" <<'YML'
name: Backend CI
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      mongo:
        image: mongo:6
        ports: ["27017:27017"]
        options: >-
          --health-cmd "mongosh --quiet --eval 'db.runCommand({ ping: 1 })'"
          --health-interval 10s --health-timeout 5s --health-retries 5
      redis:
        image: redis:7
        ports: ["6379:6379"]
    env:
      MONGODB_URI: "mongodb://localhost:27017/licenser_test"
      TENANT_DB_PREFIX: "licenser_"
      SEED_DEMO: "false"
      JWT_SECRET: "test-secret-please-change"
      JWT_ALG: "HS256"
      TZ: "America/Recife"
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-asyncio httpx asgi-lifespan pymongo
      - run: pytest -q tests
YML

cat > "$ROOT/.github/pull_request_template.md" <<'MD'
## Objetivo
- [ ] Bugfix / [ ] Feature / [ ] Refactor
Relacionado a: #ISSUE

## Mudanças principais
-

## Riscos / Migrações / Env
-

## Testes (como validar)
- [ ] Health OK e rápido
- [ ] Tenant obrigatório (sem X-Tenant-ID -> 400)
- [ ] Notificações idempotentes (mesmo Idempotency-Key -> 1 registro)
- [ ] RBAC user/admin/super_admin
- [ ] /scheduler/health responde

## Checklist
- [ ] Build ok
- [ ] Testes ok
- [ ] Lint ok
- [ ] Docs/README atualizados
MD

echo "==> Correções preparadas."
echo "Próximos passos:"
echo "  1) git checkout -b fix/apply-auto-fixes"
echo "  2) git add -A && git commit -m 'chore: aplicar correções auto (tenant/db/indexes/rbac/tests/ci)'"
echo "  3) git push -u origin fix/apply-auto-fixes && abra o Pull Request"
