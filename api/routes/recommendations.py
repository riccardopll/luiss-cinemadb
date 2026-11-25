from fastapi import APIRouter, Depends
from pydantic import BaseModel

import recommendation
from api.dependencies import Connection, current_client

router = APIRouter(tags=["recommendations"], dependencies=[Depends(current_client)])


class Interests(BaseModel):
    description: str


@router.post("/recommendations")
def recommend(interests: Interests, conn: Connection):
    return recommendation.recommend(conn, interests.description)
