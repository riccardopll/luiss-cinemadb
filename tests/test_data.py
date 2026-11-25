def fetch_all(conn, sql):
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(sql)
        return cursor.fetchall()


def test_clients_have_different_payment_methods(db):
    rows = fetch_all(
        db,
        """
        SELECT c.user_id, GROUP_CONCAT(DISTINCT pm.type ORDER BY pm.type) AS types
        FROM client c
        LEFT JOIN payment_method pm ON pm.client_id = c.user_id
        GROUP BY c.user_id
        """,
    )
    combinations = {row["types"] for row in rows}
    assert {None, "credit", "debit", "credit,debit"} <= combinations


def test_upcoming_screenings_have_different_availability(db):
    rows = fetch_all(
        db,
        """
        SELECT s.tickets_sold, t.max_occupancy - s.tickets_sold AS available_seats
        FROM screening s
        JOIN theater t ON t.id = s.theater_id
        WHERE s.starts_at > NOW()
        """,
    )
    assert any(row["tickets_sold"] == 0 for row in rows)
    assert any(row["available_seats"] == 0 for row in rows)
    assert any(row["tickets_sold"] > 0 and row["available_seats"] > 1 for row in rows)


def test_there_is_an_upcoming_screening_with_one_seat_left(db):
    rows = fetch_all(
        db,
        """
        SELECT s.id
        FROM screening s
        JOIN theater t ON t.id = s.theater_id
        WHERE s.starts_at > NOW() AND t.max_occupancy - s.tickets_sold = 1
        """,
    )
    assert rows


def test_sold_tickets_match_the_purchases(db):
    rows = fetch_all(
        db,
        """
        SELECT s.id, s.tickets_sold, COALESCE(SUM(p.num_tickets), 0) AS purchased
        FROM screening s
        LEFT JOIN purchase p ON p.screening_id = s.id
        GROUP BY s.id, s.tickets_sold
        """,
    )
    mismatched = [row["id"] for row in rows if row["tickets_sold"] != row["purchased"]]
    assert mismatched == []
