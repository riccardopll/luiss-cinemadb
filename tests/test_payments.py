import pytest

import payments
from booking import buy_tickets

GIULIA = 2
MARCO = 3
GIULIA_CREDIT_CARD = 1
MARCO_CREDIT_CARD = 3
VALID_CARD_NUMBER = "4111111111111111"
EMPTY_SCREENING = 11


@pytest.mark.parametrize(
    ("card_number", "is_valid"),
    [
        ("4526018159083012", True),
        ("4111111111111111", True),
        ("4111111111111112", False),
        ("4111-1111-1111-1111", False),
        ("411111111111", False),
        ("41111111111111111111", False),
        ("", False),
    ],
)
def test_card_number_check(card_number, is_valid):
    assert payments.card_number_is_valid(card_number) is is_valid


def test_valid_payment_method_is_added(db):
    payment_method_id = payments.add_payment_method(
        db, GIULIA, "debit", "4111 1111 1111 1111", "Via del Corso 12, 00186 Roma"
    )
    methods = payments.list_payment_methods(db, GIULIA)
    added = next(method for method in methods if method["id"] == payment_method_id)
    assert added["type"] == "debit"
    assert added["card_number"] == "**** 1111"


@pytest.mark.parametrize(
    ("payment_type", "card_number", "message"),
    [
        ("prepaid", VALID_CARD_NUMBER, "credit or debit"),
        ("credit", "4111111111111112", "Invalid card number"),
        ("credit", "not a card", "Invalid card number"),
        ("credit", "4526018159083012", "already registered"),
    ],
)
def test_invalid_payment_method_is_rejected(db, scalar, payment_type, card_number, message):
    count_before = scalar("SELECT COUNT(*) FROM payment_method")
    with pytest.raises(ValueError, match=message):
        payments.add_payment_method(db, GIULIA, payment_type, card_number)
    assert scalar("SELECT COUNT(*) FROM payment_method") == count_before


def test_unused_payment_method_is_removed(db, scalar):
    payment_method_id = payments.add_payment_method(db, GIULIA, "credit", VALID_CARD_NUMBER)
    payments.remove_payment_method(db, GIULIA, payment_method_id)
    assert scalar("SELECT COUNT(*) FROM payment_method WHERE id = %s", (payment_method_id,)) == 0


def test_payment_method_of_another_client_cannot_be_removed(db, scalar):
    with pytest.raises(ValueError, match="Invalid payment method"):
        payments.remove_payment_method(db, GIULIA, MARCO_CREDIT_CARD)
    assert scalar("SELECT COUNT(*) FROM payment_method WHERE id = %s", (MARCO_CREDIT_CARD,)) == 1


def test_used_payment_method_cannot_be_removed(db, scalar):
    with pytest.raises(ValueError, match="can't be removed"):
        payments.remove_payment_method(db, GIULIA, GIULIA_CREDIT_CARD)
    assert scalar("SELECT COUNT(*) FROM payment_method WHERE id = %s", (GIULIA_CREDIT_CARD,)) == 1


@pytest.mark.parametrize("payment_method_id", [MARCO_CREDIT_CARD, 999])
def test_purchase_with_invalid_payment_method_is_rejected(db, scalar, payment_method_id):
    purchases_before = scalar("SELECT COUNT(*) FROM purchase")
    with pytest.raises(ValueError, match="Invalid payment method"):
        buy_tickets(db, GIULIA, EMPTY_SCREENING, payment_method_id, 1)
    assert scalar("SELECT COUNT(*) FROM purchase") == purchases_before
    assert scalar("SELECT tickets_sold FROM screening WHERE id = %s", (EMPTY_SCREENING,)) == 0
