import mysql.connector
from mysql.connector import errorcode

PAYMENT_TYPES = ("credit", "debit")


def card_number_is_valid(card_number):
    if not card_number.isdigit() or not 13 <= len(card_number) <= 19:
        return False
    total = 0
    for i, digit in enumerate(reversed(card_number)):
        value = int(digit)
        if i % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def list_payment_methods(conn, client_id):
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT id, type, CONCAT('**** ', RIGHT(card_number, 4)) AS card_number, billing_address
            FROM payment_method
            WHERE client_id = %s
            ORDER BY id
            """,
            (client_id,),
        )
        return cursor.fetchall()


def add_payment_method(conn, client_id, payment_type, card_number, billing_address=None):
    card_number = card_number.replace(" ", "")
    if payment_type not in PAYMENT_TYPES:
        raise ValueError("The payment type must be credit or debit.")
    if not card_number_is_valid(card_number):
        raise ValueError("Invalid card number.")
    with conn.cursor() as cursor:
        try:
            cursor.execute(
                """
                INSERT INTO payment_method (client_id, type, card_number, billing_address)
                VALUES (%s, %s, %s, %s)
                """,
                (client_id, payment_type, card_number, billing_address or None),
            )
        except mysql.connector.IntegrityError as error:
            if error.errno == errorcode.ER_DUP_ENTRY:
                raise ValueError("This card number is already registered.") from error
            raise
        return cursor.lastrowid


def remove_payment_method(conn, client_id, payment_method_id):
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM payment_method WHERE id = %s AND client_id = %s",
            (payment_method_id, client_id),
        )
        if cursor.fetchone() is None:
            raise ValueError("Invalid payment method.")
        cursor.execute(
            "SELECT COUNT(*) FROM purchase WHERE payment_method_id = %s", (payment_method_id,)
        )
        if cursor.fetchone()[0] > 0:
            raise ValueError("This payment method was used for a purchase and can't be removed.")
        cursor.execute("DELETE FROM payment_method WHERE id = %s", (payment_method_id,))
