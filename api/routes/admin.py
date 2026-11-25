from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, NaiveDatetime

import analytics
import scheduling
from api.dependencies import Connection, current_admin

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(current_admin)])


class NewScreening(BaseModel):
    movie_id: int
    theater_id: int
    language: str
    starts_at: NaiveDatetime


@router.get("/movies")
def list_movies(conn: Connection):
    return scheduling.list_movies(conn)


@router.get("/movies/{movie_id}/languages")
def movie_languages(movie_id: int, conn: Connection):
    return scheduling.movie_languages(conn, movie_id)


@router.get("/theaters")
def list_theaters(conn: Connection):
    return scheduling.list_theaters(conn)


@router.get("/screenings")
def list_schedule(conn: Connection):
    return scheduling.list_schedule(conn)


@router.post("/screenings", status_code=status.HTTP_201_CREATED)
def add_screening(screening: NewScreening, conn: Connection):
    screening_id = scheduling.add_screening(
        conn, screening.movie_id, screening.theater_id, screening.language, screening.starts_at
    )
    return {"id": screening_id}


@router.get("/capacity")
def remaining_capacity(conn: Connection):
    return scheduling.remaining_capacity(conn)


@router.get("/analytics")
def movie_report(conn: Connection):
    return analytics.movie_report(conn)
