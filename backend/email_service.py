"""
Stub de serviço de e-mail para convites.
Em produção, integre com seu provedor (SMTP/Sendgrid/SES).
"""
from typing import Optional
import os

DEFAULT_SENDER = os.getenv("EMAIL_SENDER", "no-reply@controle-license.local")

class EmailSendError(Exception):
    pass

def send_invitation_email(to_email: str, invite_link: str, inviter_name: Optional[str] = None) -> None:
    """
    Envia (stub) e-mail de convite com link.
    Substitua por integração real; aqui apenas faz print/log.
    """
    subject = "Seu convite para acessar o sistema de licenças"
    inviter = inviter_name or "Admin"
    content = f"""
Olá,

{inviter} convidou você para acessar o sistema de licenças.
Clique no link abaixo para criar sua conta e aceitar o convite:

{invite_link}

Se você não reconhece este convite, ignore este e-mail.

Atenciosamente,
Equipe Controle-License
"""
    # Trocar por envio de e-mail real
    print(f"[email][stub] From: {DEFAULT_SENDER} To: {to_email}\nSubject: {subject}\n{content}")