"""
Testes para funcionalidade de envio em lote do WhatsApp
com idempotência, rate limiting e validação de licenças
"""

import pytest
import asyncio
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta

# Mocks para dependências
@pytest.fixture
def mock_redis():
    """Mock do Redis client"""
    redis_mock = AsyncMock()
    redis_mock.exists.return_value = False  # Para idempotência
    redis_mock.get.return_value = None  # Para rate limiting
    redis_mock.setex = AsyncMock()
    redis_mock.incr = AsyncMock()
    return redis_mock

@pytest.fixture 
def mock_db():
    """Mock do MongoDB"""
    db_mock = MagicMock()
    
    # Mock de licença válida
    valid_license = {
        "id": "license_123",
        "client_pf_id": "valid_client_123",
        "expires_at": datetime.now(timezone.utc) + timedelta(days=30)
    }
    
    # Mock de licença expirada
    expired_license = {
        "id": "license_456", 
        "client_pf_id": "expired_client_456",
        "expires_at": datetime.now(timezone.utc) - timedelta(days=10)
    }
    
    async def mock_find_one(query):
        # Simular busca de licenças
        if "valid_client_123" in str(query):
            return valid_license
        elif "expired_client_456" in str(query):
            return None  # Licença expirada não retorna resultado
        return None
    
    db_mock.licenses.find_one = AsyncMock(side_effect=mock_find_one)
    return db_mock

@pytest.fixture
def mock_whatsapp_service():
    """Mock do serviço WhatsApp Node.js"""
    service_mock = AsyncMock()
    
    # Mock de resposta bem-sucedida
    success_response = MagicMock()
    success_response.status_code = 200
    success_response.json.return_value = {"success": True, "message_id": "msg_123"}
    
    # Mock de resposta com falha
    error_response = MagicMock()
    error_response.status_code = 400
    error_response.json.return_value = {"success": False, "error": "Invalid phone number"}
    
    service_mock.post.return_value = success_response
    return service_mock

@pytest.mark.asyncio
@patch('backend.whatsapp_service.redis_client')
@patch('backend.whatsapp_service.db')
async def test_bulk_send_with_license_validation(mock_db_patch, mock_redis_patch, mock_db, mock_redis):
    """Testa envio em lote com validação de licenças"""
    mock_db_patch.return_value = mock_db
    mock_redis_patch.return_value = mock_redis
    
    from backend.whatsapp_service import WhatsAppService
    
    service = WhatsAppService()
    
    # Mock do cliente HTTP
    with patch.object(service, 'get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "message_id": "msg_123"}
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        messages = [
            {
                "phone_number": "+5511999999999", 
                "message": "Licença válida",
                "client_id": "valid_client_123",
                "message_id": "test_msg_1"
            },
            {
                "phone_number": "+5511888888888", 
                "message": "Licença expirada", 
                "client_id": "expired_client_456",
                "message_id": "test_msg_2"
            }
        ]
        
        result = await service.send_bulk_messages(messages, tenant_id="test_tenant")
        
        # Verificações
        assert result["total"] == 2
        assert result["sent"] == 1  # Apenas cliente com licença válida
        assert result["failed"] == 1  # Cliente com licença expirada
        
        # Verificar erro de licença expirada
        license_errors = [e for e in result["errors"] if e["error_type"] == "LICENSE_EXPIRED"]
        assert len(license_errors) == 1
        assert license_errors[0]["phone_number"] == "+5511888888888"

@pytest.mark.asyncio
@patch('backend.whatsapp_service.redis_client')
async def test_bulk_send_with_idempotency(mock_redis_patch, mock_redis):
    """Testa idempotência - mensagens duplicadas são ignoradas"""
    mock_redis_patch.return_value = mock_redis
    
    # Simular que mensagem já existe no Redis
    async def mock_exists(key):
        return "dup_test_123" in key
    
    mock_redis.exists.side_effect = mock_exists
    
    from backend.whatsapp_service import WhatsAppService
    
    service = WhatsAppService()
    
    with patch.object(service, 'get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        
        # Mensagens com o mesmo ID (duplicada)
        messages = [
            {
                "phone_number": "+5511999999999", 
                "message": "Mensagem original",
                "message_id": "dup_test_123"
            },
            {
                "phone_number": "+5511888888888", 
                "message": "Mensagem duplicada", 
                "message_id": "dup_test_123"  # Mesmo ID = duplicata
            }
        ]
        
        result = await service.send_bulk_messages(messages, tenant_id="test_tenant")
        
        # Verificações
        assert result["total"] == 2
        assert result["failed"] >= 1  # Pelo menos uma duplicata foi rejeitada
        
        # Verificar erro de duplicata
        duplicate_errors = [e for e in result["errors"] if e["error_type"] == "DUPLICATE"]
        assert len(duplicate_errors) >= 1

@pytest.mark.asyncio
@patch('backend.whatsapp_service.redis_client')
async def test_bulk_send_with_rate_limiting(mock_redis_patch, mock_redis):
    """Testa rate limiting - limite de 30 mensagens/minuto por tenant"""
    mock_redis_patch.return_value = mock_redis
    
    # Simular que já foram enviadas 30 mensagens
    mock_redis.get.return_value = "30"  # Rate limit atingido
    
    from backend.whatsapp_service import WhatsAppService
    
    service = WhatsAppService()
    
    with patch.object(service, 'get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        
        messages = [
            {
                "phone_number": f"+5511{i:08d}", 
                "message": f"Mensagem {i}",
                "message_id": f"rate_test_{i}"
            }
            for i in range(5)  # 5 mensagens para testar rate limit
        ]
        
        result = await service.send_bulk_messages(messages, tenant_id="test_tenant")
        
        # Verificações
        assert result["total"] == 5
        assert result["failed"] == 5  # Todas devem falhar por rate limit
        
        # Verificar erros de rate limit
        rate_limit_errors = [e for e in result["errors"] if e["error_type"] == "RATE_LIMIT"]
        assert len(rate_limit_errors) == 5

@pytest.mark.asyncio 
async def test_bulk_send_error_categorization():
    """Testa categorização correta de diferentes tipos de erro"""
    from backend.whatsapp_service import WhatsAppService, ERROR_TYPES
    
    service = WhatsAppService()
    
    # Testar se constantes de erro estão definidas corretamente
    assert "LICENSE_EXPIRED" in ERROR_TYPES
    assert "RATE_LIMIT" in ERROR_TYPES
    assert "DUPLICATE" in ERROR_TYPES
    assert "PHONE_INVALID" in ERROR_TYPES
    assert "SERVICE_ERROR" in ERROR_TYPES
    assert "TIMEOUT" in ERROR_TYPES
    
    # Verificar se mensagens de erro são descritivas
    assert "licença" in ERROR_TYPES["LICENSE_EXPIRED"].lower()
    assert "limite" in ERROR_TYPES["RATE_LIMIT"].lower()
    assert "duplicada" in ERROR_TYPES["DUPLICATE"].lower()

@pytest.mark.asyncio
async def test_bulk_send_without_redis():
    """Testa comportamento quando Redis não está disponível"""
    # Simular Redis não disponível
    with patch('backend.whatsapp_service.redis_client', None):
        from backend.whatsapp_service import WhatsAppService
        
        service = WhatsAppService()
        
        with patch.object(service, 'get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True, "message_id": "msg_123"}
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            messages = [
                {
                    "phone_number": "+5511999999999", 
                    "message": "Teste sem Redis",
                    "message_id": "no_redis_test"
                }
            ]
            
            # Deve funcionar mesmo sem Redis (sem idempotência/rate limiting)
            result = await service.send_bulk_messages(messages, tenant_id="test_tenant")
            
            assert result["total"] == 1
            # Sem Redis, não há validação de idempotência/rate limit
            # Resultado depende apenas da validação de licença e resposta do serviço

if __name__ == "__main__":
    pytest.main([__file__, "-v"])