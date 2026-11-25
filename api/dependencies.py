from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from mysql.connector.abstracts import MySQLConnectionAbstract

from database import connect


def get_connection():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def current_user(request: Request):
    user = request.session.get("user")
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Please log in.")
    return user


def current_client(user: Annotated[dict, Depends(current_user)]):
    if user["role"] != "client":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only clients can do this.")
    return user


def current_admin(user: Annotated[dict, Depends(current_user)]):
    if user["role"] != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only administrators can do this.")
    return user


Connection = Annotated[MySQLConnectionAbstract, Depends(get_connection)]
CurrentUser = Annotated[dict, Depends(current_user)]
CurrentClient = Annotated[dict, Depends(current_client)]
