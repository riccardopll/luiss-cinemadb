from datetime import date, datetime, time
from decimal import Decimal

import mysql.connector


def format_value(value):
    if value is None:
        return ""
    if isinstance(value, datetime):
        return f"{value:%Y-%m-%d %H:%M}"
    if isinstance(value, Decimal) and value.as_tuple().exponent < 0:
        return f"{value:.2f}"
    return str(value)


def yes_no(rows, *columns):
    for row in rows:
        for column in columns:
            row[column] = "yes" if row[column] else "no"
    return rows


def print_table(rows):
    if not rows:
        print("No results.")
        return
    columns = list(rows[0])
    values = [[format_value(row[column]) for column in columns] for row in rows]
    headers = [column.replace("_", " ") for column in columns]
    widths = [max(len(headers[i]), *(len(v[i]) for v in values)) for i in range(len(columns))]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths, strict=True)))
    print("  ".join("-" * w for w in widths))
    for row in values:
        print("  ".join(v.ljust(w) for v, w in zip(row, widths, strict=True)))


def ask(prompt):
    return input(prompt).strip()


def ask_int(prompt):
    text = ask(prompt)
    if not text.isdigit():
        raise ValueError("Please enter a whole number.")
    return int(text)


def ask_date(prompt):
    text = ask(prompt)
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise ValueError("Dates must be written as YYYY-MM-DD.") from None


def ask_time(prompt):
    text = ask(prompt)
    if not text:
        return None
    try:
        return time.fromisoformat(text)
    except ValueError:
        raise ValueError("Times must be written as HH:MM.") from None


def run_menu(title, options, exit_label="Exit"):
    while True:
        print(f"\n{title}")
        for number, (label, _) in enumerate(options, start=1):
            print(f"{number}. {label}")
        print(f"{len(options) + 1}. {exit_label}")
        choice = ask("> ")
        if choice == str(len(options) + 1):
            return
        if not choice.isdigit() or not 1 <= int(choice) <= len(options):
            print("Invalid choice.")
            continue
        try:
            options[int(choice) - 1][1]()
        except ValueError as error:
            print(f"Error: {error}")
        except mysql.connector.Error as error:
            print(f"Database error: {error.msg}")
