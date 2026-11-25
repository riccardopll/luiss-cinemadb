from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from api.dependencies import Connection, CurrentUser
from auth import login

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    email: str
    password: str


@router.post("/login")
def log_in(credentials: Credentials, request: Request, conn: Connection):
    user = login(conn, credentials.email, credentials.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password.")
    request.session["user"] = user
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def log_out(request: Request):
    request.session.clear()


@router.get("/me")
def me(user: CurrentUser):
    return user
