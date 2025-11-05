from __future__ import annotations

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from typing import Optional


logger = logging.getLogger("mailer")


class Mailer:
    """Lightweight SMTP mailer with graceful no-op fallback.

    Env vars:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM, SMTP_TLS (true/false)
    """

    def __init__(self) -> None:
        self.host = os.getenv("SMTP_HOST")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER")
        self.password = os.getenv("SMTP_PASS")
        self.from_addr = os.getenv("SMTP_FROM", self.user or "no-reply@dyocense.local")
        self.use_tls = os.getenv("SMTP_TLS", "true").lower() in {"1", "true", "yes", "on"}

        if not self.host:
            logger.warning("SMTP not configured; emails will be logged only.")

    def send(self, to: str, subject: str, text: str, html: Optional[str] = None) -> None:
        if not self.host:
            logger.info("[EMAIL:LOG] to=%s subject=%s body=%s", to, subject, text)
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = to

        part1 = MIMEText(text, "plain")
        msg.attach(part1)
        if html:
            part2 = MIMEText(html, "html")
            msg.attach(part2)

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.sendmail(self.from_addr, [to], msg.as_string())
        except Exception as exc:
            logger.warning("Failed to send email to %s: %s", to, exc)
