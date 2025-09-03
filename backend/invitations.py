import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional, Dict, Any

SECRET = (os.getenv("INVITE_SECRET") or os.getenv("SECRET_KEY") or "dev-secret").encode("utf-8")
DEFAULT_TTL_SECONDS = int(os.getenv("INVITE_TTL_SECONDS", "604800"))  # 7 dias

def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def b64url_decode(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def sign_invite(payload: Dict[str, Any]) -> str:
    """
    Gera um token HMAC-SHA256 (header.payload.signature) em base64url.
    """
    header = {"alg": "HS256", "typ": "INV"}
    header_b64 = b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    sig = hmac.new(SECRET, signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{b64url(sig)}"

def verify_invite(token: str) -> Dict[str, Any]:
    """
    Verifica assinatura e expiração. Retorna o payload se OK; senão lança ValueError.
    """
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected = hmac.new(SECRET, signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, b64url_decode(sig_b64)):
            raise ValueError("Assinatura inválida")
        payload = json.loads(b64url_decode(payload_b64))
        if "exp" in payload and int(payload["exp"]) < int(time.time()):
            raise ValueError("Convite expirado")
        return payload
    except Exception as e:
        raise ValueError(f"Token inválido: {e}")

def generate_invite_token(email: str, tenant_id: str, admin_vendor_id: str, ttl_seconds: Optional[int] = None) -> str:
    now = int(time.time())
    exp = now + int(ttl_seconds or DEFAULT_TTL_SECONDS)
    payload = {
        "sub": "invite",
        "email": email.lower().strip(),
        "tenant_id": tenant_id,
        "admin_vendor_id": admin_vendor_id,
        "iat": now,
        "exp": exp,
        "v": 1,
    }
    return sign_invite(payload)

def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()