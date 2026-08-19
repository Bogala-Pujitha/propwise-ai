"""Minimal SMTP email delivery using Python's standard library.

No third-party mail package is required.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def send_password_reset_email(
    *,
    recipient: str,
    reset_url: str,
) -> bool:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM") or username

    if not host or not sender:
        return False

    message = EmailMessage()
    message["Subject"] = "PropWise AI password reset"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        "A password reset was requested for your PropWise AI account.\n\n"
        f"Reset your password using this link:\n{reset_url}\n\n"
        "The link expires after 30 minutes. If you did not request this, "
        "you can ignore this email."
    )

    with smtplib.SMTP(host, port, timeout=20) as server:
        server.starttls()
        if username and password:
            server.login(username, password)
        server.send_message(message)

    return True
