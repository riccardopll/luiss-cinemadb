import pytest

import main
from auth import login

CLIENT_PASSWORD = "cinema123"
ADMIN_PASSWORD = "asqlroma"


def test_client_logs_in(db):
    user = login(db, "giulia.rossi@example.com", CLIENT_PASSWORD)
    assert user == {"id": 2, "role": "client", "name": "Giulia Rossi"}


def test_administrator_logs_in(db):
    user = login(db, "admin@example.com", ADMIN_PASSWORD)
    assert user == {"id": 1, "role": "admin", "name": None}


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("giulia.rossi@example.com", "wrong-password"),
        ("giulia.rossi@example.com", ""),
        ("giulia.rossi@example.com", ADMIN_PASSWORD),
        ("nobody@example.com", CLIENT_PASSWORD),
        ("", ""),
    ],
)
def test_invalid_login_is_rejected(db, email, password):
    assert login(db, email, password) is None


def test_three_failed_attempts_end_the_login(db, monkeypatch):
    attempts = []
    monkeypatch.setattr(main, "ask", lambda prompt: "giulia.rossi@example.com")
    monkeypatch.setattr(main, "getpass", lambda prompt: attempts.append(prompt) or "wrong")
    assert main.ask_credentials(db) is None
    assert len(attempts) == main.MAX_LOGIN_ATTEMPTS
