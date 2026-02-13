"""
PDF Generator for Certificates - License Manager v1.4.0
Gera PDFs profissionais a partir de templates HTML
"""
import os
import io
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

# Diretório de templates
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')


class CertificatePDFGenerator:
    """Gerador de PDFs para certificados"""
    
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=True
        )
    
    def generate_certificate_pdf(
        self,
        certificate: Dict[str, Any],
        company_name: Optional[str] = None
    ) -> bytes:
        """
        Gera PDF do certificado
        
        Args:
            certificate: Dados do certificado
            company_name: Nome da empresa (para branding)
        
        Returns:
            bytes: Conteúdo do PDF
        """
        # Carregar template
        template = self.env.get_template('certificate_template.html')
        
        # Calcular dias de validade
        activation = certificate.get('activation_date')
        expiration = certificate.get('expiration_date')
        
        if isinstance(activation, str):
            activation = datetime.fromisoformat(activation.replace('Z', '+00:00'))
        if isinstance(expiration, str):
            expiration = datetime.fromisoformat(expiration.replace('Z', '+00:00'))
        
        days_validity = (expiration - activation).days if activation and expiration else 365
        
        # Renderizar HTML
        html_content = template.render(
            certificate=certificate,
            company_name=company_name or os.environ.get('COMPANY_NAME', 'LICENSE MANAGER'),
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
        Gera PDF simplificado (apenas páginas 1 e 2)
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
        
        return self.generate_certificate_pdf(certificate, company_name)


# Instância global
pdf_generator = CertificatePDFGenerator()


def generate_pdf(certificate_data: Dict[str, Any], company_name: Optional[str] = None) -> bytes:
    """Função utilitária para gerar PDF"""
    return pdf_generator.generate_certificate_pdf(certificate_data, company_name)
