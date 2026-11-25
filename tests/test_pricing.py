from datetime import date
from decimal import Decimal

import pytest

import scheduling
from pricing import ticket_price

SCREENING_DATE = date(2026, 12, 1)
RECENT_RELEASE = date(2026, 1, 1)
OLD_RELEASE = date(2020, 1, 1)


@pytest.mark.parametrize(
    ("supports_3d", "has_enhanced_sound", "release_date", "price"),
    [
        (False, False, RECENT_RELEASE, "15.00"),
        (True, False, RECENT_RELEASE, "20.00"),
        (False, True, RECENT_RELEASE, "18.00"),
        (True, True, RECENT_RELEASE, "23.00"),
        (False, False, OLD_RELEASE, "12.00"),
        (True, False, OLD_RELEASE, "16.00"),
        (False, True, OLD_RELEASE, "14.40"),
        (True, True, OLD_RELEASE, "18.40"),
    ],
)
def test_ticket_price_rules(supports_3d, has_enhanced_sound, release_date, price):
    assert ticket_price(supports_3d, has_enhanced_sound, release_date, SCREENING_DATE) == Decimal(
        price
    )


@pytest.mark.parametrize(
    ("release_date", "screening_date", "price"),
    [
        (date(2024, 12, 1), date(2026, 12, 1), "15.00"),
        (date(2024, 11, 30), date(2026, 12, 1), "12.00"),
        (date(2026, 2, 28), date(2028, 2, 29), "15.00"),
        (date(2026, 2, 27), date(2028, 2, 29), "12.00"),
    ],
    ids=[
        "released exactly two years before",
        "released one day earlier",
        "leap day, exactly two years before",
        "leap day, one day earlier",
    ],
)
def test_discount_starts_after_two_years(release_date, screening_date, price):
    assert ticket_price(False, False, release_date, screening_date) == Decimal(price)


def test_search_shows_the_same_price_as_the_purchase(db):
    with db.cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT s.id, s.starts_at, t.supports_3d, t.has_enhanced_sound, m.release_date
            FROM screening s
            JOIN theater t ON t.id = s.theater_id
            JOIN movie m ON m.id = s.movie_id
            """
        )
        screenings = {row["id"]: row for row in cursor.fetchall()}
    results = scheduling.search_screenings(db)
    assert results
    for result in results:
        screening = screenings[result["id"]]
        expected = ticket_price(
            screening["supports_3d"],
            screening["has_enhanced_sound"],
            screening["release_date"],
            screening["starts_at"].date(),
        )
        assert result["ticket_price"] == expected
