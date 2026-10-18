"""Outbound email via Resend.

When ``RESEND_API_KEY`` is unset (local dev, tests) the magic link is logged
instead of sent, so the auth flow works without an email provider.
"""

import logging

import resend

from config import settings

logger = logging.getLogger(__name__)


def send_magic_link(email: str, link: str) -> None:
    """Email a sign-in link to ``email``. Raises RuntimeError if Resend fails."""
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY unset; magic link for %s: %s", email, link)
        print(f"[magic link] {email}: {link}", flush=True)
        return

    resend.api_key = settings.resend_api_key
    try:
        resend.Emails.send(
            {
                "from": settings.email_from,
                "to": [email],
                "subject": "Your Slipstream sign-in link",
                "text": (
                    f"Sign in to Slipstream:\n\n{link}\n\n"
                    "This link expires in 15 minutes and can be used once. "
                    "If you didn't request it, ignore this email."
                ),
                "html": (
                    f'<p><a href="{link}">Sign in to Slipstream</a></p>'
                    "<p>This link expires in 15 minutes and can be used once. "
                    "If you didn't request it, ignore this email.</p>"
                ),
            }
        )
    except Exception as exc:  # Resend raises several error types; normalise them.
        raise RuntimeError("Failed to send magic-link email") from exc
