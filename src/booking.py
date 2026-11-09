from pricing import ticket_price


def buy_tickets(conn, client_id, screening_id, payment_method_id, num_tickets):
    if num_tickets < 1:
        raise ValueError("The number of tickets must be at least 1.")
    with conn.cursor(dictionary=True) as cursor:
        conn.start_transaction()
        try:
            cursor.execute(
                "SELECT id FROM payment_method WHERE id = %s AND client_id = %s",
                (payment_method_id, client_id),
            )
            if cursor.fetchone() is None:
                raise ValueError("Invalid payment method.")

            cursor.execute(
                """
                SELECT
                    s.starts_at,
                    s.starts_at <= NOW() AS started,
                    s.tickets_sold,
                    t.max_occupancy,
                    t.supports_3d,
                    t.has_enhanced_sound,
                    m.release_date
                FROM screening s
                JOIN theater t ON t.id = s.theater_id
                JOIN movie m ON m.id = s.movie_id
                WHERE s.id = %s
                FOR UPDATE OF s
                """,
                (screening_id,),
            )
            screening = cursor.fetchone()
            if screening is None:
                raise ValueError(f"Screening {screening_id} does not exist.")
            if screening["started"]:
                raise ValueError("This screening has already started.")
            available = screening["max_occupancy"] - screening["tickets_sold"]
            if num_tickets > available:
                raise ValueError(f"Not enough seats: {available} left for this screening.")

            price = ticket_price(
                screening["supports_3d"],
                screening["has_enhanced_sound"],
                screening["release_date"],
                screening["starts_at"].date(),
            )
            total_amount = price * num_tickets
            cursor.execute(
                """
                INSERT INTO purchase (screening_id, payment_method_id, num_tickets, total_amount)
                VALUES (%s, %s, %s, %s)
                """,
                (screening_id, payment_method_id, num_tickets, total_amount),
            )
            purchase_id = cursor.lastrowid
            cursor.execute(
                "UPDATE screening SET tickets_sold = tickets_sold + %s WHERE id = %s",
                (num_tickets, screening_id),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return {"id": purchase_id, "num_tickets": num_tickets, "total_amount": total_amount}


def purchase_history(conn, client_id):
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT
                p.id,
                p.purchased_at,
                m.title,
                s.theater_id,
                s.starts_at,
                l.name AS language,
                p.num_tickets,
                p.total_amount,
                pm.type AS card_type,
                RIGHT(pm.card_number, 4) AS card_last_digits
            FROM purchase p
            JOIN payment_method pm ON pm.id = p.payment_method_id
            JOIN screening s ON s.id = p.screening_id
            JOIN movie m ON m.id = s.movie_id
            JOIN language l ON l.id = s.language_id
            WHERE pm.client_id = %s
            ORDER BY p.purchased_at DESC
            """,
            (client_id,),
        )
        return cursor.fetchall()
