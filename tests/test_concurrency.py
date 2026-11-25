import threading
import time

from booking import buy_tickets

ONE_SEAT_LEFT_SCREENING = 9
THEATER_CAPACITY = 10
GIULIA = 2
GIULIA_CREDIT_CARD = 1
MARCO = 3
MARCO_CREDIT_CARD = 3
LOCK_HOLD_SECONDS = 1


class SlowLockCursor:
    def __init__(self, cursor, lock_taken):
        self.cursor = cursor
        self.lock_taken = lock_taken

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        self.cursor.close()

    def execute(self, sql, params=()):
        self.cursor.execute(sql, params)
        if "max_occupancy" in sql:
            self.lock_taken.set()
            time.sleep(LOCK_HOLD_SECONDS)

    def __getattr__(self, name):
        return getattr(self.cursor, name)


class SlowLockConnection:
    def __init__(self, conn, lock_taken):
        self.conn = conn
        self.lock_taken = lock_taken

    def cursor(self, **options):
        return SlowLockCursor(self.conn.cursor(**options), self.lock_taken)

    def __getattr__(self, name):
        return getattr(self.conn, name)


def test_concurrent_purchase_of_the_last_seat(db, connect, scalar):
    lock_taken = threading.Event()
    first_conn = SlowLockConnection(connect(), lock_taken)
    second_conn = connect()
    results = {}

    def first_purchase():
        results["first"] = buy_tickets(
            first_conn, GIULIA, ONE_SEAT_LEFT_SCREENING, GIULIA_CREDIT_CARD, 1
        )

    def second_purchase():
        lock_taken.wait(timeout=10)
        try:
            results["second"] = buy_tickets(
                second_conn, MARCO, ONE_SEAT_LEFT_SCREENING, MARCO_CREDIT_CARD, 1
            )
        except ValueError as error:
            results["second"] = error

    purchases_before = scalar(
        "SELECT COUNT(*) FROM purchase WHERE screening_id = %s", (ONE_SEAT_LEFT_SCREENING,)
    )
    threads = [threading.Thread(target=first_purchase), threading.Thread(target=second_purchase)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert results["first"]["num_tickets"] == 1
    assert isinstance(results["second"], ValueError)
    assert "Not enough seats: 0 left" in str(results["second"])
    assert (
        scalar("SELECT tickets_sold FROM screening WHERE id = %s", (ONE_SEAT_LEFT_SCREENING,))
        == THEATER_CAPACITY
    )
    assert (
        scalar("SELECT COUNT(*) FROM purchase WHERE screening_id = %s", (ONE_SEAT_LEFT_SCREENING,))
        == purchases_before + 1
    )
    assert (
        scalar(
            "SELECT COUNT(*) FROM purchase WHERE screening_id = %s AND payment_method_id = %s",
            (ONE_SEAT_LEFT_SCREENING, MARCO_CREDIT_CARD),
        )
        == 0
    )
