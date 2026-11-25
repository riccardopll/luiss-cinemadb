from fastapi import APIRouter, status
from pydantic import BaseModel

import booking
from api.dependencies import Connection, CurrentClient

router = APIRouter(prefix="/purchases", tags=["purchases"])


class PurchaseRequest(BaseModel):
    screening_id: int
    payment_method_id: int
    num_tickets: int


@router.get("")
def purchase_history(conn: Connection, client: CurrentClient):
    return booking.purchase_history(conn, client["id"])


@router.post("", status_code=status.HTTP_201_CREATED)
def buy_tickets(purchase: PurchaseRequest, conn: Connection, client: CurrentClient):
    return booking.buy_tickets(
        conn,
        client["id"],
        purchase.screening_id,
        purchase.payment_method_id,
        purchase.num_tickets,
    )
