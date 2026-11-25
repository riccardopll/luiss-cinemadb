from datetime import date, time

from fastapi import APIRouter, Depends

import scheduling
from api.dependencies import Connection, current_client

router = APIRouter(tags=["screenings"], dependencies=[Depends(current_client)])


@router.get("/screenings")
def search_screenings(
    conn: Connection,
    title: str | None = None,
    genre: str | None = None,
    language: str | None = None,
    day: date | None = None,
    start_time: time | None = None,
):
    return scheduling.search_screenings(conn, title, genre, language, day, start_time)


@router.get("/genres")
def list_genres(conn: Connection):
    return scheduling.list_genres(conn)


@router.get("/languages")
def list_languages(conn: Connection):
    return scheduling.list_languages(conn)
