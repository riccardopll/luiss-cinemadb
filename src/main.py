from getpass import getpass

import mysql.connector

import admin
import client
from auth import login
from database import connect
from ui import ask

MAX_LOGIN_ATTEMPTS = 3


def ask_credentials(conn):
    for _ in range(MAX_LOGIN_ATTEMPTS):
        email = ask("Email: ")
        password = getpass("Password: ")
        user = login(conn, email, password)
        if user is not None:
            return user
        print("Invalid email or password.")
    return None


def main():
    try:
        conn = connect()
    except mysql.connector.Error as error:
        print(f"Cannot connect to the database: {error.msg}")
        return
    try:
        user = ask_credentials(conn)
        if user is None:
            print("Too many failed attempts.")
        elif user["role"] == "admin":
            admin.menu(conn)
        else:
            client.menu(conn, user)
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        conn.close()
    print("Goodbye.")


if __name__ == "__main__":
    main()
