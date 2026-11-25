import pytest

import recommendation

MOVIE_COUNT = 30
EMBEDDING_DIMENSIONS = 1024


@pytest.fixture
def embedded_db(db):
    recommendation.embed_movies(db)
    return db


def test_movie_text_uses_title_year_genres_and_description(db):
    texts = recommendation.movie_texts(db)
    assert texts[1].startswith(
        "Project Hail Mary (2026). Adventure, Science Fiction. Science teacher"
    )
    assert len(texts) == MOVIE_COUNT


def test_movie_text_without_genres():
    assert recommendation.movie_text("Title", 2020, None, "Description.") == (
        "Title (2020). Description."
    )


def test_every_movie_gets_one_embedding(embedded_db, scalar):
    assert scalar("SELECT COUNT(*) FROM movie_embedding") == MOVIE_COUNT
    assert scalar("SELECT MIN(VECTOR_DIM(embedding)) FROM movie_embedding") == EMBEDDING_DIMENSIONS
    assert scalar("SELECT MAX(VECTOR_DIM(embedding)) FROM movie_embedding") == EMBEDDING_DIMENSIONS


def test_embedding_again_replaces_the_embeddings(embedded_db, scalar):
    assert recommendation.embed_movies(embedded_db) == MOVIE_COUNT
    assert scalar("SELECT COUNT(*) FROM movie_embedding") == MOVIE_COUNT


def test_three_movies_from_the_database_are_recommended(embedded_db, scalar):
    movies = recommendation.recommend(embedded_db, "a quiet drama about family")
    assert len(movies) == recommendation.RECOMMENDATION_COUNT
    for movie in movies:
        assert scalar("SELECT title FROM movie WHERE id = %s", (movie["id"],)) == movie["title"]
    similarities = [movie["similarity"] for movie in movies]
    assert similarities == sorted(similarities, reverse=True)


@pytest.mark.parametrize(
    ("description", "title"),
    [
        ("an astronaut who must save the sun", "Project Hail Mary"),
        ("an astronaut stranded on Mars who has to survive alone", "The Martian"),
        ("un astronauta bloccato su Marte che deve sopravvivere", "The Martian"),
        ("a mafia family saga", "The Godfather"),
        ("una saga su una famiglia mafiosa", "The Godfather"),
        ("toys that come to life", "Toy Story"),
        ("a love story between a jazz musician and an actress", "La La Land"),
    ],
)
def test_best_match_comes_first(embedded_db, description, title):
    assert recommendation.recommend(embedded_db, description)[0]["title"] == title


def test_fewer_than_three_movies_returns_all_of_them(embedded_db):
    with embedded_db.cursor() as cursor:
        cursor.execute("DELETE FROM movie_embedding WHERE movie_id NOT IN (1, 2)")
    movies = recommendation.recommend(embedded_db, "space")
    assert sorted(movie["id"] for movie in movies) == [1, 2]


@pytest.mark.parametrize("description", ["", "   "])
def test_empty_description_is_rejected(embedded_db, description):
    with pytest.raises(ValueError, match="describe"):
        recommendation.recommend(embedded_db, description)


def test_missing_embeddings_are_reported(db):
    with pytest.raises(ValueError, match="cinema embed"):
        recommendation.recommend(db, "space")
