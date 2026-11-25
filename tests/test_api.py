from datetime import date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient

import recommendation
from api.dependencies import get_connection
from api.main import app

CLIENT_LOGIN = {"email": "giulia.rossi@example.com", "password": "cinema123"}
ADMIN_LOGIN = {"email": "admin@example.com", "password": "asqlroma"}
GIULIA_CREDIT_CARD = 1
EMPTY_SCREENING = 11
TOY_STORY = 29
SMALL_THEATER = 1


@pytest.fixture
def api(db, connect):
    app.dependency_overrides[get_connection] = connect
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def client_api(api):
    api.post("/api/auth/login", json=CLIENT_LOGIN).raise_for_status()
    return api


@pytest.fixture
def admin_api(api):
    api.post("/api/auth/login", json=ADMIN_LOGIN).raise_for_status()
    return api


def starts_at(days_from_today, hour):
    return datetime.combine(date.today() + timedelta(days=days_from_today), time(hour)).isoformat()


def test_login_sets_the_session_and_logout_clears_it(api):
    response = api.post("/api/auth/login", json=CLIENT_LOGIN)
    assert response.status_code == 200
    assert response.json() == {"id": 2, "role": "client", "name": "Giulia Rossi"}
    assert api.get("/api/auth/me").json()["id"] == 2
    assert api.post("/api/auth/logout").status_code == 204
    assert api.get("/api/auth/me").status_code == 401


def test_invalid_login_is_rejected(api):
    response = api.post("/api/auth/login", json={**CLIENT_LOGIN, "password": "wrong"})
    assert response.status_code == 401
    assert api.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/screenings"),
        ("get", "/api/purchases"),
        ("get", "/api/payment-methods"),
        ("post", "/api/recommendations"),
        ("get", "/api/admin/analytics"),
    ],
)
def test_routes_need_a_login(api, method, path):
    assert api.request(method, path).status_code == 401


def test_client_cannot_use_admin_routes(client_api):
    assert client_api.get("/api/admin/analytics").status_code == 403


def test_admin_cannot_buy_tickets(admin_api):
    response = admin_api.post(
        "/api/purchases",
        json={"screening_id": EMPTY_SCREENING, "payment_method_id": 1, "num_tickets": 1},
    )
    assert response.status_code == 403


def test_client_buys_tickets_and_sees_the_purchase(client_api):
    response = client_api.post(
        "/api/purchases",
        json={
            "screening_id": EMPTY_SCREENING,
            "payment_method_id": GIULIA_CREDIT_CARD,
            "num_tickets": 2,
        },
    )
    assert response.status_code == 201
    purchase = response.json()
    assert purchase["total_amount"] == 24
    history = client_api.get("/api/purchases").json()
    assert history[0]["id"] == purchase["id"]


def test_rejected_purchase_returns_the_reason(client_api):
    response = client_api.post(
        "/api/purchases",
        json={
            "screening_id": EMPTY_SCREENING,
            "payment_method_id": GIULIA_CREDIT_CARD,
            "num_tickets": 11,
        },
    )
    assert response.status_code == 400
    assert "Not enough seats" in response.json()["detail"]


def test_search_filters_screenings(client_api):
    screenings = client_api.get("/api/screenings", params={"title": "Cinema Paradiso"}).json()
    assert screenings
    assert {screening["title"] for screening in screenings} == {"Cinema Paradiso"}


def test_client_adds_and_removes_a_payment_method(client_api):
    response = client_api.post(
        "/api/payment-methods", json={"type": "debit", "card_number": "4111 1111 1111 1111"}
    )
    assert response.status_code == 201
    payment_method_id = response.json()["id"]
    methods = client_api.get("/api/payment-methods").json()
    card_numbers = {method["id"]: method["card_number"] for method in methods}
    assert card_numbers[payment_method_id] == "**** 1111"
    assert client_api.delete(f"/api/payment-methods/{payment_method_id}").status_code == 204


def test_invalid_payment_method_is_rejected(client_api):
    response = client_api.post(
        "/api/payment-methods", json={"type": "debit", "card_number": "4111111111111112"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid card number."


def test_admin_adds_a_screening(admin_api):
    response = admin_api.post(
        "/api/admin/screenings",
        json={
            "movie_id": TOY_STORY,
            "theater_id": SMALL_THEATER,
            "language": "English",
            "starts_at": starts_at(10, 14),
        },
    )
    assert response.status_code == 201
    schedule_ids = [screening["id"] for screening in admin_api.get("/api/admin/screenings").json()]
    assert response.json()["id"] in schedule_ids


def test_admin_cannot_add_a_screening_in_the_past(admin_api):
    response = admin_api.post(
        "/api/admin/screenings",
        json={
            "movie_id": TOY_STORY,
            "theater_id": SMALL_THEATER,
            "language": "English",
            "starts_at": starts_at(-1, 14),
        },
    )
    assert response.status_code == 400
    assert "future" in response.json()["detail"]


@pytest.mark.parametrize("path", ["capacity", "analytics", "movies", "theaters"])
def test_admin_reports_are_returned(admin_api, path):
    response = admin_api.get(f"/api/admin/{path}")
    assert response.status_code == 200
    assert response.json()


def test_client_gets_three_recommendations(db, client_api):
    recommendation.embed_movies(db)
    response = client_api.post(
        "/api/recommendations",
        json={"description": "an astronaut stranded on Mars who has to survive alone"},
    )
    assert response.status_code == 200
    movies = response.json()
    assert len(movies) == 3
    assert movies[0]["title"] == "The Martian"
