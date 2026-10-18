"""Outbound email via Resend.

When ``RESEND_API_KEY`` is unset (local dev, tests) emails are logged instead
of sent, so the auth flow and reminders work without an email provider.
"""

import logging
import time
from datetime import datetime
from html import escape

import resend

from config import settings

logger = logging.getLogger(__name__)

# Resend allows 2 requests/second; space out batches (lineup reminders).
MIN_SEND_INTERVAL = 0.6
_last_send = 0.0


def _send(email: str, subject: str, text: str, html: str) -> bool:
    """Send one email: True once Resend accepts it, False if it was only
    logged (no API key). Raises RuntimeError if Resend fails."""
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY unset; email to %s: %s", email, subject)
        print(f"[email] {email}: {subject}\n{text}", flush=True)
        return False

    global _last_send
    time.sleep(max(0.0, _last_send + MIN_SEND_INTERVAL - time.monotonic()))
    _last_send = time.monotonic()
    resend.api_key = settings.resend_api_key
    try:
        resend.Emails.send(
            {"from": settings.email_from, "to": [email], "subject": subject, "text": text, "html": html}
        )
    except Exception as exc:  # Resend raises several error types; normalise them.
        # Callers only show a generic message, so record Resend's reason
        # (e.g. unverified sender domain) where the logs can see it.
        logger.exception("Resend failed to send %r from %r: %s", subject, settings.email_from, exc)
        raise RuntimeError(f"Failed to send email: {subject}") from exc
    return True


def send_magic_link(email: str, link: str) -> None:
    """Email a sign-in link to ``email``. Raises RuntimeError if Resend fails."""
    _send(
        email,
        "Your Slipstream sign-in link",
        f"Sign in to Slipstream:\n\n{link}\n\n"
        "This link expires in 15 minutes and can be used once. "
        "If you didn't request it, ignore this email.",
        f'<p><a href="{link}">Sign in to Slipstream</a></p>'
        "<p>This link expires in 15 minutes and can be used once. "
        "If you didn't request it, ignore this email.</p>",
    )


def send_lineup_reminder(email: str, username: str, race_name: str, lockdown_at: datetime,
                         missing: list[str], link: str) -> bool:
    """Remind a user their team for ``race_name`` is incomplete before it
    locks. ``missing`` reads like ["2 drivers", "a constructor"]. Returns
    whether it was really sent (see ``_send``); raises RuntimeError if Resend
    fails."""
    gaps = " and ".join(missing)
    when = lockdown_at.strftime("%a %d %b, %H:%M UTC")
    return _send(
        email,
        f"Your {race_name} lineup needs {gaps}",
        f"Hi {username},\n\nYour Slipstream team for the {race_name} still needs {gaps}. "
        f"Lineups lock {when}.\n\nSet your team: {link}",
        f"<p>Hi {escape(username)},</p><p>Your Slipstream team for the {escape(race_name)} "
        f"still needs <strong>{escape(gaps)}</strong>. Lineups lock {when}.</p>"
        f'<p><a href="{link}">Set your team</a></p>',
    )
