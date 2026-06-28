"""
Dead Man's Switch — Delivery Engine
SMTP email delivery using Python stdlib only (smtplib + email.mime).
"""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List


def _build_email(sender: str, recipient: Dict[str, str], message: Dict[str, str]) -> MIMEMultipart:
    """Construct a MIME email from a message dict."""
    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = f"{recipient['name']} <{recipient['email']}>"
    msg["Subject"] = message.get("subject", "Message automatique — Dead Man's Switch")
    body = message.get("body", "")
    msg.attach(MIMEText(body, "plain", "utf-8"))
    return msg


def send_messages(cfg: Dict[str, Any]) -> List[str]:
    """
    Send all configured messages to all configured recipients via SMTP TLS.

    Returns a list of error strings (empty list = all succeeded).
    """
    smtp_cfg = cfg.get("smtp", {})
    host = smtp_cfg.get("host", "")
    port = int(smtp_cfg.get("port", 587))
    user = smtp_cfg.get("user", "")
    password = smtp_cfg.get("password", "")
    recipients = cfg.get("recipients", [])
    messages = cfg.get("messages", [])
    errors: List[str] = []

    if not host or not user or not password:
        return ["SMTP non configuré — impossible d'envoyer les messages."]
    if not recipients:
        return ["Aucun destinataire configuré."]
    if not messages:
        return ["Aucun message configuré."]

    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()  # RFC 3207 §3: re-issue EHLO after TLS to refresh capability list
            server.login(user, password)
            for recipient in recipients:
                for message in messages:
                    try:
                        email = _build_email(user, recipient, message)
                        server.sendmail(user, recipient["email"], email.as_string())
                    except Exception as exc:
                        errors.append(
                            f"Échec envoi à {recipient['email']}: {exc}"
                        )
    except smtplib.SMTPAuthenticationError:
        errors.append("Authentification SMTP échouée — vérifiez votre mot de passe.")
    except Exception as exc:
        errors.append(f"Erreur SMTP: {exc}")

    return errors


def test_smtp(cfg: Dict[str, Any]) -> List[str]:
    """Send a test email to the sender's own address to verify SMTP settings."""
    smtp_cfg = cfg.get("smtp", {})
    user = smtp_cfg.get("user", "")
    test_recipient = {"name": "Moi-même", "email": user}
    test_message = {
        "subject": "Test — Dead Man's Switch",
        "body": "Si vous recevez cet email, votre configuration SMTP fonctionne correctement.",
    }
    test_cfg = dict(cfg)
    test_cfg["recipients"] = [test_recipient]
    test_cfg["messages"] = [test_message]
    return send_messages(test_cfg)
