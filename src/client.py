import booking
import payments
import scheduling
from ui import ask, ask_date, ask_int, ask_time, print_table, run_menu, yes_no


def search(conn):
    print("Leave a criterion blank to ignore it.")
    title = ask("Title: ") or None
    print("Genres: " + ", ".join(scheduling.list_genres(conn)))
    genre = ask("Genre: ") or None
    print("Languages: " + ", ".join(scheduling.list_languages(conn)))
    language = ask("Language: ") or None
    day = ask_date("Date (YYYY-MM-DD): ")
    start_time = ask_time("From time (HH:MM): ")
    rows = scheduling.search_screenings(conn, title, genre, language, day, start_time)
    print_table(yes_no(rows, "supports_3d", "has_enhanced_sound"))


def buy(conn, client_id):
    methods = payments.list_payment_methods(conn, client_id)
    if not methods:
        print("You have no payment methods. Add one first.")
        return
    screening_id = ask_int("Screening id: ")
    num_tickets = ask_int("Number of tickets: ")
    print_table(methods)
    payment_method_id = ask_int("Payment method id: ")
    purchase = booking.buy_tickets(conn, client_id, screening_id, payment_method_id, num_tickets)
    print(
        f"Purchase {purchase['id']} completed. Tickets: {purchase['num_tickets']}, "
        f"total: {purchase['total_amount']:.2f} EUR."
    )


def add_payment_method(conn, client_id):
    payment_type = ask("Type (credit or debit): ").lower()
    card_number = ask("Card number: ")
    billing_address = ask("Billing address (optional): ") or None
    payment_method_id = payments.add_payment_method(
        conn, client_id, payment_type, card_number, billing_address
    )
    print(f"Payment method {payment_method_id} added.")


def remove_payment_method(conn, client_id):
    print_table(payments.list_payment_methods(conn, client_id))
    payment_method_id = ask_int("Payment method id to remove: ")
    payments.remove_payment_method(conn, client_id, payment_method_id)
    print(f"Payment method {payment_method_id} removed.")


def manage_payment_methods(conn, client_id):
    run_menu(
        "Payment methods",
        [
            (
                "List payment methods",
                lambda: print_table(payments.list_payment_methods(conn, client_id)),
            ),
            ("Add a payment method", lambda: add_payment_method(conn, client_id)),
            ("Remove a payment method", lambda: remove_payment_method(conn, client_id)),
        ],
        exit_label="Back",
    )


def recommendations():
    print("Movie recommendations are not available yet.")


def menu(conn, user):
    client_id = user["id"]
    run_menu(
        f"Client menu ({user['name']})",
        [
            ("Search movie screenings", lambda: search(conn)),
            ("Buy tickets", lambda: buy(conn, client_id)),
            (
                "View previous purchases",
                lambda: print_table(booking.purchase_history(conn, client_id)),
            ),
            ("Manage payment methods", lambda: manage_payment_methods(conn, client_id)),
            ("Get movie recommendations", recommendations),
        ],
    )
