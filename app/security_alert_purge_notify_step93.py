"""Notification SMTP opt-in lors d'un échec de purge planifiée.

Aucune notification réseau sans activation explicite. Aucun détail d'exception,
identifiant de compte ou secret dans le message.
"""
import os
import smtplib
import ssl
from email.message import EmailMessage


def notify_failure(*, error_code='PURGE_FAILED'):
    """Retourne 'disabled' ou 'sent'; lève en cas de configuration/SMTP invalide."""
    if os.getenv('BOUKOULOU_PURGE_FAILURE_NOTIFY', '').strip().lower() != 'enabled':
        return 'disabled'
    if error_code not in {'PURGE_FAILED', 'AUDIT_FAILED'}:
        raise ValueError('Code de notification non autorisé')
    host = os.getenv('BOUKOULOU_PURGE_SMTP_HOST', '').strip()
    sender = os.getenv('BOUKOULOU_PURGE_SMTP_FROM', '').strip()
    recipient = os.getenv('BOUKOULOU_PURGE_SMTP_TO', '').strip()
    username = os.getenv('BOUKOULOU_PURGE_SMTP_USER', '').strip()
    password = os.getenv('BOUKOULOU_PURGE_SMTP_PASSWORD', '')
    port_raw = os.getenv('BOUKOULOU_PURGE_SMTP_PORT', '465')
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise ValueError('Port SMTP invalide') from exc
    if not host or not sender or not recipient or not 1 <= port <= 65535:
        raise ValueError('Configuration SMTP incomplète')
    if any('\n' in x or '\r' in x for x in (host, sender, recipient, username)):
        raise ValueError('Configuration SMTP invalide')
    if bool(username) != bool(password):
        raise ValueError('Authentification SMTP incomplète')
    # Une seule adresse destinataire; aucune injection d'en-têtes.
    if ',' in recipient or ';' in recipient or '@' not in recipient or '@' not in sender:
        raise ValueError('Adresse SMTP invalide')
    msg = EmailMessage()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = '[Boukoulou Transport] Echec de purge des alertes'
    msg.set_content('Une purge planifiée des alertes de sécurité a échoué.\n'
                    f'Code : {error_code}\n'
                    'Consultez les journaux du planificateur et l’historique administrateur.\n'
                    'Aucune donnée sensible ni exception brute n’est transmise.\n')
    with smtplib.SMTP_SSL(host, port, timeout=10, context=ssl.create_default_context()) as smtp:
        if username:
            smtp.login(username, password)
        smtp.send_message(msg)
    return 'sent'
