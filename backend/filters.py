from typing import Dict, Any, Iterable

FORBIDDEN_OPERATORS = {"$where", "$regex", "$ne", "$in", "$nin", "$gt", "$gte", "$lt", "$lte", "$or", "$and", "$nor"}

def whitelist_filter(payload: Dict[str, Any], allowed_fields: Iterable[str]) -> Dict[str, Any]:
    """
    Constrói um filtro seguro a partir de um dicionário vindo do cliente,
    mantendo somente campos explicitamente permitidos e rejeitando operadores perigosos.
    """
    if not payload:
        return {}

    allowed = set(allowed_fields or [])
    out: Dict[str, Any] = {}
    for k, v in payload.items():
        if not isinstance(k, str):
            continue
        if k.startswith("$") or k in FORBIDDEN_OPERATORS:
            # rejeita operadores
            continue
        if k not in allowed:
            # campo não permitido
            continue
        out[k] = v
    return out

def merge_with_scope(user_scope: Dict[str, Any], client_filter: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mescla o filtro do escopo do usuário (tenant, seller/assigned) com o filtro do cliente (já whitelitado).
    Em caso de colisão de chaves, o ESCOPO prevalece para evitar bypass.
    """
    out = dict(client_filter or {})
    for k, v in (user_scope or {}).items():
        out[k] = v
    return out