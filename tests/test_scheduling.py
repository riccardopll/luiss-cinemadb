from datetime import date, datetime, time, timedelta

import pytest

import scheduling

TOY_STORY = 29
CINEMA_PARADISO = 19
SMALL_THEATER = 1
YESTERDAY = date.today() - timedelta(days=1)
TOMORROW = date.today() + timedelta(days=1)
FREE_DAY = date.today() + timedelta(days=10)


def at(day, hour, minute=0):
    return datetime.combine(day, time(hour, minute))


def test_valid_screening_is_added(db, scalar):
    screening_id = scheduling.add_screening(
        db, TOY_STORY, SMALL_THEATER, "English", at(FREE_DAY, 14)
    )
    assert scalar("SELECT movie_id FROM screening WHERE id = %s", (screening_id,)) == TOY_STORY


@pytest.mark.parametrize(
    "starts_at",
    [at(TOMORROW, 22, 6), at(TOMORROW, 18, 29)],
    ids=["10 minutes after the 20:00 screening ends", "ends 10 minutes before it starts"],
)
def test_screening_exactly_ten_minutes_apart_is_added(db, starts_at):
    scheduling.add_screening(db, TOY_STORY, SMALL_THEATER, "English", starts_at)


@pytest.mark.parametrize(
    ("movie_id", "theater_id", "language", "starts_at", "message"),
    [
        (TOY_STORY, SMALL_THEATER, "English", at(TOMORROW, 20), "is busy"),
        (TOY_STORY, SMALL_THEATER, "English", at(TOMORROW, 21), "is busy"),
        (TOY_STORY, SMALL_THEATER, "English", at(TOMORROW, 22, 5), "is busy"),
        (TOY_STORY, SMALL_THEATER, "English", at(TOMORROW, 18, 30), "is busy"),
        (TOY_STORY, SMALL_THEATER, "English", at(FREE_DAY, 9, 30), "outside the opening hours"),
        (TOY_STORY, SMALL_THEATER, "English", at(FREE_DAY, 22, 40), "outside the opening hours"),
        (TOY_STORY, SMALL_THEATER, "English", at(YESTERDAY, 14), "must start in the future"),
        (CINEMA_PARADISO, SMALL_THEATER, "English", at(FREE_DAY, 14), "not available in English"),
        (999, SMALL_THEATER, "English", at(FREE_DAY, 14), "Movie 999 does not exist"),
        (TOY_STORY, 99, "English", at(FREE_DAY, 14), "Theater 99 does not exist"),
    ],
    ids=[
        "same start time",
        "overlapping",
        "9 minutes after the previous screening",
        "9 minutes before the next screening",
        "before opening",
        "ends after closing",
        "in the past",
        "language not available",
        "unknown movie",
        "unknown theater",
    ],
)
def test_invalid_or_overlapping_screening_is_rejected(
    db, scalar, movie_id, theater_id, language, starts_at, message
):
    screenings_before = scalar("SELECT COUNT(*) FROM screening")
    with pytest.raises(ValueError, match=message):
        scheduling.add_screening(db, movie_id, theater_id, language, starts_at)
    assert scalar("SELECT COUNT(*) FROM screening") == screenings_before
