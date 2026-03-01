"""Email service — IMAP fetch + SMTP send (async)."""

import asyncio
import email
import imaplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional
from loguru import logger
from config import settings

_executor = ThreadPoolExecutor(max_workers=2)


class EmailService:
    """Fetch emails via IMAP and send via SMTP."""

    def _fetch_emails(
        self,
        host: str, port: int, user: str, password: str,
        folder: str = "INBOX", limit: int = 20, since: str = None
    ) -> list[dict]:
        """Synchronous IMAP fetch."""
        try:
            mail = imaplib.IMAP4_SSL(host, port)
            mail.login(user, password)
            mail.select(folder)

            criteria = "ALL"
            if since:
                criteria = f'(SINCE "{since}")'

            status, messages = mail.search(None, criteria)
            if status != "OK":
                return []

            msg_ids = messages[0].split()
            msg_ids = msg_ids[-limit:]  # latest N

            results = []
            for mid in reversed(msg_ids):
                status, data = mail.fetch(mid, "(RFC822)")
                if status != "OK":
                    continue
                raw = data[0][1]
                msg = email.message_from_bytes(raw)

                body = ""
                html_body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        ct = part.get_content_type()
                        if ct == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="replace")
                        elif ct == "text/html":
                            html_body = part.get_payload(decode=True).decode(errors="replace")
                else:
                    body = msg.get_payload(decode=True).decode(errors="replace")

                date_str = msg.get("Date", "")
                try:
                    parsed_date = email.utils.parsedate_to_datetime(date_str)
                except Exception:
                    parsed_date = datetime.utcnow()

                results.append({
                    "message_id": msg.get("Message-ID", ""),
                    "from": msg.get("From", ""),
                    "to": msg.get("To", ""),
                    "subject": msg.get("Subject", ""),
                    "body_text": body[:5000],
                    "body_html": html_body[:10000],
                    "date": parsed_date.isoformat(),
                })

            mail.logout()
            return results
        except Exception as e:
            logger.error("IMAP fetch error: {}", e)
            return []

    async def fetch_emails(self, host: str = None, port: int = None,
                           user: str = None, password: str = None,
                           limit: int = 20) -> list[dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, self._fetch_emails,
            host or settings.IMAP_HOST,
            port or settings.IMAP_PORT,
            user or settings.IMAP_USER,
            password or settings.IMAP_PASSWORD,
            "INBOX", limit, None
        )

    def _send_email(self, host: str, port: int, user: str, password: str,
                    to: str, subject: str, body: str, html: bool = False) -> bool:
        """Synchronous SMTP send."""
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = user
            msg["To"] = to
            msg["Subject"] = subject

            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(host, port)
            server.starttls()
            server.login(user, password)
            server.sendmail(user, to, msg.as_string())
            server.quit()
            logger.info("Email sent to {}", to)
            return True
        except Exception as e:
            logger.error("SMTP send error: {}", e)
            return False

    async def send_email(self, to: str, subject: str, body: str,
                         host: str = None, port: int = None,
                         user: str = None, password: str = None,
                         html: bool = False) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, self._send_email,
            host or settings.SMTP_HOST,
            port or settings.SMTP_PORT,
            user or settings.SMTP_USER,
            password or settings.SMTP_PASSWORD,
            to, subject, body, html
        )


email_service = EmailService()
