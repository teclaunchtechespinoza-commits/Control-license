"""
PDF Generator for Certificates - License Manager v1.5.0
Gera PDFs profissionais a partir de templates HTML com suporte a configurações dinâmicas
"""
import os
import io
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

# Diretório de templates
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')


class CertificatePDFGenerator:
    """Gerador de PDFs para certificados com configurações dinâmicas"""
    
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=True
        )
    
    def generate_certificate_pdf(
        self,
        certificate: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Gera PDF do certificado com configurações do tenant
        
        Args:
            certificate: Dados do certificado
            settings: Configurações de certificado do tenant (logo, termos, procedimento)
        
        Returns:
            bytes: Conteúdo do PDF
        """
        # Carregar template
        template = self.env.get_template('certificate_template_v2.html')
        
        # Calcular dias de validade
        activation = certificate.get('activation_date')
        expiration = certificate.get('expiration_date')
        
        if isinstance(activation, str):
            activation = datetime.fromisoformat(activation.replace('Z', '+00:00'))
        if isinstance(expiration, str):
            expiration = datetime.fromisoformat(expiration.replace('Z', '+00:00'))
        
        days_validity = (expiration - activation).days if activation and expiration else 365
        
        # Configurações padrão
        default_settings = {
            'company_name': os.environ.get('COMPANY_NAME', 'LICENSE MANAGER'),
            'company_subtitle': None,
            'logo_base64': None,
            'primary_color': '#22c55e',
            'secondary_color': '#3b82f6',
            'background_color': '#0a0a0a',
            'terms': {
                'introduction': 'Este termo estabelece as condições de uso da licença de acesso ao sistema.',
                'sections': []
            },
            'procedure_title': 'PROCEDIMENTO DE ATIVAÇÃO',
            'procedure_subtitle': 'Siga os passos abaixo para ativar seu acesso',
            'prerequisites': [
                'Equipamento compatível com número de série válido',
                'Conexão com a internet estável',
                'Credenciais de acesso (fornecidas neste certificado)'
            ],
            'procedure_steps': [],
            'important_info': [
                'Mantenha este certificado em seus arquivos.',
                'Consulte nossa documentação ou suporte técnico em caso de dúvidas.',
                'O acesso é de uso exclusivo e intransferível.',
                'Mantenha seu equipamento atualizado.'
            ]
        }
        
        # Mesclar com configurações fornecidas
        if settings:
            for key, value in settings.items():
                if value is not None:
                    default_settings[key] = value
        
        # Renderizar HTML
        html_content = template.render(
            certificate=certificate,
            settings=default_settings,
            days_validity=days_validity,
            generated_at=datetime.now(timezone.utc)
        )
        
        # Converter para PDF
        html = HTML(string=html_content)
        pdf_bytes = html.write_pdf()
        
        return pdf_bytes
    
    def generate_simple_certificate(
        self,
        client_name: str,
        product_name: str,
        serial_number: str,
        expiration_date: datetime,
        certificate_number: str,
        qr_code_data: str,
        credentials: Optional[Dict[str, str]] = None,
        company_name: Optional[str] = None
    ) -> bytes:
        """
        Gera PDF simplificado (compatibilidade com versão anterior)
        """
        certificate = {
            'client_name': client_name,
            'product_name': product_name,
            'serial_number': serial_number,
            'expiration_date': expiration_date,
            'activation_date': datetime.now(timezone.utc),
            'issued_at': datetime.now(timezone.utc),
            'issued_by_name': 'Sistema',
            'certificate_number': certificate_number,
            'qr_code_data': qr_code_data,
            'region': 'América do Norte',
            'hash': 'auto-generated',
            'credentials': credentials
        }
        
        settings = {'company_name': company_name} if company_name else None
        
        return self.generate_certificate_pdf(certificate, settings)


# Instância global
pdf_generator = CertificatePDFGenerator()


def generate_pdf(certificate_data: Dict[str, Any], settings: Optional[Dict[str, Any]] = None) -> bytes:
    """Função utilitária para gerar PDF"""
    return pdf_generator.generate_certificate_pdf(certificate_data, settings)
