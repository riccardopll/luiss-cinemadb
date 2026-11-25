import sys
from getpass import getpass

import mysql.connector

import admin
import client
import recommendation
from auth import login
from database import connect
from ui import ask

MAX_LOGIN_ATTEMPTS = 3
USAGE = "Usage: cinema [embed]"


def ask_credentials(conn):
    for _ in range(MAX_LOGIN_ATTEMPTS):
        email = ask("Email: ")
        password = getpass("Password: ")
        user = login(conn, email, password)
        if user is not None:
            return user
        print("Invalid email or password.")
    return None


def run_session(conn):
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
    print("Goodbye.")


def embed_movies(conn):
    count = recommendation.embed_movies(conn)
    print(f"Stored embeddings for {count} movies with {recommendation.MODEL_NAME}.")


def main():
    arguments = sys.argv[1:]
    if arguments not in ([], ["embed"]):
        print(USAGE)
        return
    try:
        conn = connect()
    except mysql.connector.Error as error:
        print(f"Cannot connect to the database: {error.msg}")
        return
    try:
        if arguments == ["embed"]:
            embed_movies(conn)
        else:
            run_session(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
