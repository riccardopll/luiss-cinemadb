from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

import config
from api.routes import admin, auth, payment_methods, purchases, recommendations, screenings

app = FastAPI(title="Cinema API")
app.add_middleware(SessionMiddleware, secret_key=config.SESSION_SECRET)

for route_module in (auth, screenings, purchases, payment_methods, recommendations, admin):
    app.include_router(route_module.router, prefix="/api")


@app.exception_handler(ValueError)
def rejected_request(request: Request, error: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(error)})
