"""Email service fallback (no Resend key → link is logged, nothing sent)."""

import pytest

from services import email


def test_magic_link_is_printed_when_resend_key_unset(monkeypatch, capsys):
    monkeypatch.setattr(email.settings, "resend_api_key", None)

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("Resend must not be called without an API key")

    monkeypatch.setattr(email.resend.Emails, "send", fail)
    email.send_magic_link("a@example.com", "http://localhost:5173/auth/verify?token=abc")
    assert "token=abc" in capsys.readouterr().out


def test_resend_failure_raises_runtime_error(monkeypatch, caplog):
    monkeypatch.setattr(email.settings, "resend_api_key", "re_test")

    def boom(params: object) -> None:
        raise ValueError("bad request")

    monkeypatch.setattr(email.resend.Emails, "send", boom)
    with pytest.raises(RuntimeError):
        email.send_magic_link("a@example.com", "http://x/auth/verify?token=abc")
    # Resend's reason must reach the logs; the API response stays generic.
    assert "bad request" in caplog.text
