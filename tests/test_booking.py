from decimal import Decimal

import mysql.connector
import pytest

from booking import buy_tickets, purchase_history

GIULIA = 2
GIULIA_CREDIT_CARD = 1
MARCO = 3
PAST_SCREENING = 1
ONE_SEAT_LEFT_SCREENING = 9
SOLD_OUT_SCREENING = 10
EMPTY_SCREENING = 11


class FailingUpdateCursor:
    def __init__(self, cursor, executed):
        self.cursor = cursor
        self.executed = executed

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        self.cursor.close()

    def execute(self, sql, params=()):
        statement = " ".join(sql.split())
        self.executed.append(statement)
        if statement.startswith("UPDATE screening"):
            raise mysql.connector.DatabaseError("Simulated failure while updating the screening.")
        self.cursor.execute(sql, params)

    def __getattr__(self, name):
        return getattr(self.cursor, name)


class FailingUpdateConnection:
    def __init__(self, conn):
        self.conn = conn
        self.executed = []

    def cursor(self, **options):
        return FailingUpdateCursor(self.conn.cursor(**options), self.executed)

    def __getattr__(self, name):
        return getattr(self.conn, name)


def screening_state(scalar, screening_id):
    return (
        scalar("SELECT tickets_sold FROM screening WHERE id = %s", (screening_id,)),
        scalar("SELECT COUNT(*) FROM purchase WHERE screening_id = %s", (screening_id,)),
    )


def test_purchase_is_stored_and_updates_sold_tickets(db, scalar):
    purchase = buy_tickets(db, GIULIA, EMPTY_SCREENING, GIULIA_CREDIT_CARD, 2)
    assert purchase["num_tickets"] == 2
    assert purchase["total_amount"] == Decimal("24.00")
    assert screening_state(scalar, EMPTY_SCREENING) == (2, 1)
    assert scalar("SELECT total_amount FROM purchase WHERE id = %s", (purchase["id"],)) == Decimal(
        "24.00"
    )


def test_last_seat_can_be_bought(db, scalar):
    buy_tickets(db, GIULIA, ONE_SEAT_LEFT_SCREENING, GIULIA_CREDIT_CARD, 1)
    tickets_sold = scalar(
        "SELECT tickets_sold FROM screening WHERE id = %s", (ONE_SEAT_LEFT_SCREENING,)
    )
    assert tickets_sold == 10


@pytest.mark.parametrize(
    ("screening_id", "num_tickets", "message"),
    [
        (ONE_SEAT_LEFT_SCREENING, 2, "Not enough seats: 1 left"),
        (SOLD_OUT_SCREENING, 1, "Not enough seats: 0 left"),
        (EMPTY_SCREENING, 11, "Not enough seats: 10 left"),
    ],
)
def test_more_tickets_than_available_are_rejected(db, scalar, screening_id, num_tickets, message):
    state_before = screening_state(scalar, screening_id)
    with pytest.raises(ValueError, match=message):
        buy_tickets(db, GIULIA, screening_id, GIULIA_CREDIT_CARD, num_tickets)
    assert screening_state(scalar, screening_id) == state_before


@pytest.mark.parametrize(
    ("screening_id", "num_tickets", "message"),
    [
        (EMPTY_SCREENING, 0, "at least 1"),
        (999, 1, "does not exist"),
        (PAST_SCREENING, 1, "already started"),
    ],
)
def test_invalid_purchase_is_rejected(db, scalar, screening_id, num_tickets, message):
    purchases_before = scalar("SELECT COUNT(*) FROM purchase")
    with pytest.raises(ValueError, match=message):
        buy_tickets(db, GIULIA, screening_id, GIULIA_CREDIT_CARD, num_tickets)
    assert scalar("SELECT COUNT(*) FROM purchase") == purchases_before


def test_failed_transaction_is_rolled_back(db, scalar):
    failing_conn = FailingUpdateConnection(db)
    with pytest.raises(mysql.connector.DatabaseError, match="Simulated failure"):
        buy_tickets(failing_conn, GIULIA, EMPTY_SCREENING, GIULIA_CREDIT_CARD, 2)
    assert any(statement.startswith("INSERT INTO purchase") for statement in failing_conn.executed)
    assert screening_state(scalar, EMPTY_SCREENING) == (0, 0)
    buy_tickets(db, GIULIA, EMPTY_SCREENING, GIULIA_CREDIT_CARD, 2)
    assert screening_state(scalar, EMPTY_SCREENING) == (2, 1)


def test_purchase_history_lists_only_the_clients_purchases(db):
    purchase = buy_tickets(db, GIULIA, EMPTY_SCREENING, GIULIA_CREDIT_CARD, 1)
    giulia_purchase_ids = [row["id"] for row in purchase_history(db, GIULIA)]
    marco_purchase_ids = [row["id"] for row in purchase_history(db, MARCO)]
    assert giulia_purchase_ids[0] == purchase["id"]
    assert purchase["id"] not in marco_purchase_ids
    assert set(giulia_purchase_ids).isdisjoint(marco_purchase_ids)
