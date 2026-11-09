from datetime import datetime

import analytics
import scheduling
from ui import ask, ask_date, ask_int, ask_time, print_table, run_menu, yes_no


def add_screening(conn):
    print_table(scheduling.list_movies(conn))
    movie_id = ask_int("Movie id: ")
    languages = scheduling.movie_languages(conn, movie_id)
    if not languages:
        raise ValueError(f"Movie {movie_id} does not exist.")
    print("Available languages: " + ", ".join(languages))
    language = ask("Language: ")
    print_table(yes_no(scheduling.list_theaters(conn), "supports_3d", "has_enhanced_sound"))
    theater_id = ask_int("Theater id: ")
    day = ask_date("Date (YYYY-MM-DD): ")
    start_time = ask_time("Start time (HH:MM): ")
    if day is None or start_time is None:
        raise ValueError("A date and a start time are required.")
    starts_at = datetime.combine(day, start_time)
    screening_id = scheduling.add_screening(conn, movie_id, theater_id, language, starts_at)
    print(f"Screening {screening_id} added.")


def menu(conn):
    run_menu(
        "Administrator menu",
        [
            ("Add a movie screening", lambda: add_screening(conn)),
            ("View the screening schedule", lambda: print_table(scheduling.list_schedule(conn))),
            ("View remaining capacity", lambda: print_table(scheduling.remaining_capacity(conn))),
            ("View analytics", lambda: print_table(analytics.movie_report(conn))),
        ],
    )
