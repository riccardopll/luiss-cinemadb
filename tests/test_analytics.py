from decimal import Decimal

from analytics import movie_report
from booking import buy_tickets

GIULIA = 2
GIULIA_CREDIT_CARD = 1
UPCOMING_PROJECT_HAIL_MARY = 12
UPCOMING_CINEMA_PARADISO = 11


def report_by_title(conn):
    return {row["title"]: row for row in movie_report(conn)}


def test_revenue_counts_all_tickets_while_occupancy_uses_started_screenings(db):
    before = report_by_title(db)
    assert before["Cinema Paradiso"]["tickets_sold"] == 0
    assert before["Cinema Paradiso"]["revenue"] == Decimal("0.00")
    assert before["Cinema Paradiso"]["average_occupancy_percent"] is None

    hail_mary_before = before["Project Hail Mary"]
    assert hail_mary_before["average_occupancy_percent"] is not None

    buy_tickets(db, GIULIA, UPCOMING_CINEMA_PARADISO, GIULIA_CREDIT_CARD, 2)
    buy_tickets(db, GIULIA, UPCOMING_PROJECT_HAIL_MARY, GIULIA_CREDIT_CARD, 1)

    after = report_by_title(db)
    assert after["Cinema Paradiso"]["tickets_sold"] == 2
    assert after["Cinema Paradiso"]["revenue"] == Decimal("24.00")
    assert after["Cinema Paradiso"]["average_occupancy_percent"] is None

    hail_mary_after = after["Project Hail Mary"]
    assert hail_mary_after["tickets_sold"] == hail_mary_before["tickets_sold"] + 1
    assert hail_mary_after["revenue"] == hail_mary_before["revenue"] + Decimal("23.00")
    assert (
        hail_mary_after["average_occupancy_percent"]
        == hail_mary_before["average_occupancy_percent"]
    )
