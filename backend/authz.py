from enum import Enum
from typing import Dict, Any

class Role(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    USER = "USER"

def build_scope_filter(current_user, base: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Centraliza RBAC (papel) + ABAC (atributos) para filtrar dados por escopo.

    Regras:
      - SUPER_ADMIN: acesso amplo (sem restrição de tenant) — ajuste se desejar limitar por tenant.
      - ADMIN: restringe por tenant_id (CORRIGIDO: removido filtro seller_admin_id para permitir admin ver todas as licenças do tenant)
      - USER: restringe por tenant_id e assigned_user_id = current_user.id
    """
    q: Dict[str, Any] = dict(base or {})

    if getattr(current_user, "role", None) == Role.SUPER_ADMIN:
        # Atenção: se quiser restringir por tenant mesmo para SUPER_ADMIN, descomente:
        # if hasattr(current_user, "tenant_id"):
        #     q["tenant_id"] = current_user.tenant_id
        return q

    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        # Segurança defensiva: se não houver tenant no usuário, não retorna dados.
        # Alternativamente, poderia levantar uma exceção HTTP 400/403 no chamador.
        q["tenant_id"] = "__INVALID__"
        return q

    q["tenant_id"] = tenant_id
    # CORRIGIDO: Admin vê todas as licenças do tenant (não filtrar por created_by/seller_admin_id)
    # Isolamento é feito por tenant_id, não por admin individual
    if getattr(current_user, "role", None) == Role.USER:
        q["assigned_user_id"] = getattr(current_user, "id", None)

    return q

def enforce_object_scope(obj: Dict[str, Any], current_user) -> bool:
    """
    Checagem rápida de escopo para objetos individuais (além do filtro de consulta).
    Retorna True se o objeto está no escopo do usuário.
    
    CORRIGIDO: Admin pode acessar qualquer objeto do seu tenant (não verificar seller_admin_id)
    """
    role = getattr(current_user, "role", None)
    if role == Role.SUPER_ADMIN:
        return True

    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id or obj.get("tenant_id") != tenant_id:
        return False

    # CORRIGIDO: Admin pode acessar qualquer objeto do seu tenant
    if role == Role.ADMIN:
        return True  # Admin tem acesso completo ao tenant
    
    # USER só vê objetos atribuídos a ele
    if role == Role.USER:
        return obj.get("assigned_user_id") == getattr(current_user, "id", None)

    return False