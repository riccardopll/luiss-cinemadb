import os
from pathlib import Path

import mysql.connector
import pytest

import config

ROOT_DIR = Path(__file__).resolve().parent.parent
TEST_DB_NAME = "cinema_test"


def connect_as_root(database=None):
    return mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user="root",
        password=os.getenv("MYSQL_ROOT_PASSWORD", "root"),
        database=database,
        autocommit=True,
    )


def run_sql_file(conn, path):
    with conn.cursor() as cursor:
        cursor.execute(path.read_text(), map_results=True)
        for _ in cursor.fetchsets():
            pass


def reset_test_database():
    with connect_as_root() as conn, conn.cursor() as cursor:
        cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
        cursor.execute(f"CREATE DATABASE {TEST_DB_NAME}")
    with connect_as_root(TEST_DB_NAME) as conn:
        run_sql_file(conn, ROOT_DIR / "schema.sql")
        run_sql_file(conn, ROOT_DIR / "data.sql")


@pytest.fixture
def connect():
    connections = []

    def open_connection():
        conn = connect_as_root(TEST_DB_NAME)
        connections.append(conn)
        return conn

    yield open_connection
    for conn in connections:
        conn.close()


@pytest.fixture
def db(connect):
    reset_test_database()
    return connect()


@pytest.fixture
def scalar(db):
    def run(sql, params=()):
        with db.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()[0]

    return run
