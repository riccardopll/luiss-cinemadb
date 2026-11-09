from datetime import datetime, time, timedelta

OPENING_TIME = time(10, 0)
CLOSING_TIME = time(23, 59)


def fetch_all(conn, sql, params=()):
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def list_movies(conn):
    return fetch_all(conn, "SELECT id, title, running_time_minutes FROM movie ORDER BY title")


def list_theaters(conn):
    return fetch_all(
        conn,
        "SELECT id, max_occupancy, supports_3d, has_enhanced_sound FROM theater ORDER BY id",
    )


def list_genres(conn):
    return [row["name"] for row in fetch_all(conn, "SELECT name FROM genre ORDER BY name")]


def list_languages(conn):
    return [row["name"] for row in fetch_all(conn, "SELECT name FROM language ORDER BY name")]


def movie_languages(conn, movie_id):
    rows = fetch_all(
        conn,
        """
        SELECT l.name
        FROM movie_language ml
        JOIN language l ON l.id = ml.language_id
        WHERE ml.movie_id = %s
        ORDER BY l.name
        """,
        (movie_id,),
    )
    return [row["name"] for row in rows]


def search_screenings(conn, title=None, genre=None, language=None, day=None, start_time=None):
    return fetch_all(
        conn,
        """
        SELECT
            s.id,
            m.title,
            s.theater_id,
            s.starts_at,
            l.name AS language,
            ROUND(
                (15
                 + CASE WHEN t.supports_3d THEN 5 ELSE 0 END
                 + CASE WHEN t.has_enhanced_sound THEN 3 ELSE 0 END)
                * CASE WHEN m.release_date < DATE(s.starts_at) - INTERVAL 2 YEAR
                       THEN 0.8 ELSE 1 END,
                2
            ) AS ticket_price,
            t.max_occupancy - s.tickets_sold AS available_seats,
            t.supports_3d,
            t.has_enhanced_sound
        FROM screening s
        JOIN movie m ON m.id = s.movie_id
        JOIN theater t ON t.id = s.theater_id
        JOIN language l ON l.id = s.language_id
        WHERE s.starts_at > NOW()
          AND (%(title)s IS NULL OR m.title LIKE CONCAT('%', %(title)s, '%'))
          AND (%(genre)s IS NULL OR m.id IN (
                SELECT mg.movie_id
                FROM movie_genre mg
                JOIN genre g ON g.id = mg.genre_id
                WHERE g.name = %(genre)s))
          AND (%(language)s IS NULL OR l.name = %(language)s)
          AND (%(date)s IS NULL OR DATE(s.starts_at) = %(date)s)
          AND (%(time)s IS NULL OR TIME(s.starts_at) >= %(time)s)
        ORDER BY s.starts_at, s.theater_id
        """,
        {"title": title, "genre": genre, "language": language, "date": day, "time": start_time},
    )


def list_schedule(conn):
    return fetch_all(
        conn,
        """
        SELECT
            s.id,
            m.title,
            s.theater_id,
            l.name AS language,
            s.starts_at,
            s.starts_at + INTERVAL m.running_time_minutes MINUTE AS ends_at
        FROM screening s
        JOIN movie m ON m.id = s.movie_id
        JOIN language l ON l.id = s.language_id
        WHERE s.starts_at > NOW()
        ORDER BY s.starts_at, s.theater_id
        """,
    )


def remaining_capacity(conn):
    return fetch_all(
        conn,
        """
        SELECT
            s.id,
            m.title,
            s.theater_id,
            s.starts_at,
            s.tickets_sold,
            t.max_occupancy,
            t.max_occupancy - s.tickets_sold AS remaining_seats,
            ROUND(100 * s.tickets_sold / t.max_occupancy, 1) AS occupancy_percent
        FROM screening s
        JOIN movie m ON m.id = s.movie_id
        JOIN theater t ON t.id = s.theater_id
        WHERE s.starts_at > NOW()
        ORDER BY s.starts_at, s.theater_id
        """,
    )


def add_screening(conn, movie_id, theater_id, language, starts_at):
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT running_time_minutes FROM movie WHERE id = %s", (movie_id,))
        movie = cursor.fetchone()
        if movie is None:
            raise ValueError(f"Movie {movie_id} does not exist.")

        cursor.execute("SELECT id FROM theater WHERE id = %s", (theater_id,))
        if cursor.fetchone() is None:
            raise ValueError(f"Theater {theater_id} does not exist.")

        cursor.execute(
            """
            SELECT l.id
            FROM movie_language ml
            JOIN language l ON l.id = ml.language_id
            WHERE ml.movie_id = %s AND l.name = %s
            """,
            (movie_id, language),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"The movie is not available in {language}.")
        language_id = row["id"]

        ends_at = starts_at + timedelta(minutes=movie["running_time_minutes"])
        closing = datetime.combine(starts_at.date(), CLOSING_TIME)
        if starts_at.time() < OPENING_TIME or ends_at > closing:
            raise ValueError(
                f"The screening would run from {starts_at:%H:%M} to {ends_at:%H:%M}, "
                f"outside the opening hours ({OPENING_TIME:%H:%M} to {CLOSING_TIME:%H:%M})."
            )

        conn.start_transaction()
        try:
            cursor.execute("SELECT id FROM theater WHERE id = %s FOR UPDATE", (theater_id,))
            cursor.fetchone()
            cursor.execute(
                """
                SELECT
                    s.id,
                    m.title,
                    s.starts_at,
                    s.starts_at + INTERVAL m.running_time_minutes MINUTE AS ends_at
                FROM screening s
                JOIN movie m ON m.id = s.movie_id
                WHERE s.theater_id = %(theater_id)s
                  AND s.starts_at < %(starts_at)s + INTERVAL (
                        SELECT running_time_minutes FROM movie WHERE id = %(movie_id)s) + 10 MINUTE
                  AND s.starts_at + INTERVAL m.running_time_minutes + 10 MINUTE > %(starts_at)s
                """,
                {"theater_id": theater_id, "starts_at": starts_at, "movie_id": movie_id},
            )
            conflicts = cursor.fetchall()
            if conflicts:
                busy = ", ".join(
                    f"{c['title']} {c['starts_at']:%H:%M}-{c['ends_at']:%H:%M}" for c in conflicts
                )
                raise ValueError(
                    f"Theater {theater_id} is busy ({busy}). "
                    "Screenings must be at least 10 minutes apart."
                )
            cursor.execute(
                """
                INSERT INTO screening (movie_id, theater_id, language_id, starts_at)
                VALUES (%s, %s, %s, %s)
                """,
                (movie_id, theater_id, language_id, starts_at),
            )
            screening_id = cursor.lastrowid
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return screening_id
