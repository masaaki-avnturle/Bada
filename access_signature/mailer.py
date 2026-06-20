"""Email delivery for the gatekeeper.

If SMTP is configured via environment variables it sends real mail; otherwise
it *spools* the message to a file and returns the path (a safe default so
nothing is sent without credentials).  Either way every message is logged.

Environment variables (all required to actually send):
    SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASS,
    SMTP_FROM (default = SMTP_USER), SMTP_TLS (default "1")
"""

from __future__ import annotations

import os
import smtplib
import time
from email.message import EmailMessage


class Mailer:
    def __init__(self, spool_dir: str):
        self.spool_dir = spool_dir
        self.log: list[str] = []

    def _smtp_configured(self) -> bool:
        return all(os.environ.get(k) for k in
                   ("SMTP_HOST", "SMTP_USER", "SMTP_PASS"))

    def send(self, to: str, subject: str, body: str) -> str:
        sender = os.environ.get("SMTP_FROM") or os.environ.get(
            "SMTP_USER", "no-reply@access-signature.local")
        if self._smtp_configured():
            return self._send_smtp(sender, to, subject, body)
        return self._spool(sender, to, subject, body)

    # -- real send ---------------------------------------------------------
    def _send_smtp(self, sender: str, to: str, subject: str,
                   body: str) -> str:
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        host = os.environ["SMTP_HOST"]
        port = int(os.environ.get("SMTP_PORT", "587"))
        with smtplib.SMTP(host, port) as s:
            if os.environ.get("SMTP_TLS", "1") == "1":
                s.starttls()
            s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            s.send_message(msg)
        self.log.append(f"SENT to {to}: {subject}")
        return f"smtp:{host}"

    # -- safe spool fallback ----------------------------------------------
    def _spool(self, sender: str, to: str, subject: str, body: str) -> str:
        os.makedirs(self.spool_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        slug = "".join(c if c.isalnum() else "-" for c in subject)[:48]
        path = os.path.join(self.spool_dir, f"{ts}_{slug}.eml")
        n = 1
        while os.path.exists(path):                # avoid same-second clashes
            path = os.path.join(self.spool_dir, f"{ts}_{slug}_{n}.eml")
            n += 1
        with open(path, "w") as f:
            f.write(f"From: {sender}\nTo: {to}\nSubject: {subject}\n\n{body}\n")
        self.log.append(f"SPOOLED to {to}: {subject} -> {path}")
        return path
