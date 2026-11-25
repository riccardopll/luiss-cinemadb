from fastapi import APIRouter, status
from pydantic import BaseModel

import payments
from api.dependencies import Connection, CurrentClient

router = APIRouter(prefix="/payment-methods", tags=["payment methods"])


class NewPaymentMethod(BaseModel):
    type: str
    card_number: str
    billing_address: str | None = None


@router.get("")
def list_payment_methods(conn: Connection, client: CurrentClient):
    return payments.list_payment_methods(conn, client["id"])


@router.post("", status_code=status.HTTP_201_CREATED)
def add_payment_method(payment_method: NewPaymentMethod, conn: Connection, client: CurrentClient):
    payment_method_id = payments.add_payment_method(
        conn,
        client["id"],
        payment_method.type.lower(),
        payment_method.card_number,
        payment_method.billing_address,
    )
    return {"id": payment_method_id}


@router.delete("/{payment_method_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_payment_method(payment_method_id: int, conn: Connection, client: CurrentClient):
    payments.remove_payment_method(conn, client["id"], payment_method_id)
