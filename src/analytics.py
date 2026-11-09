def movie_report(conn):
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT
                m.title,
                COUNT(*) AS screenings,
                SUM(s.tickets_sold) AS tickets_sold,
                ROUND(100 * AVG(s.tickets_sold / t.max_occupancy), 1) AS average_occupancy_percent,
                SUM(COALESCE(r.revenue, 0)) AS revenue
            FROM screening s
            JOIN movie m ON m.id = s.movie_id
            JOIN theater t ON t.id = s.theater_id
            LEFT JOIN (
                SELECT screening_id, SUM(total_amount) AS revenue
                FROM purchase
                GROUP BY screening_id
            ) r ON r.screening_id = s.id
            WHERE s.starts_at < NOW()
            GROUP BY m.id, m.title
            ORDER BY revenue DESC, m.title
            """
        )
        return cursor.fetchall()
