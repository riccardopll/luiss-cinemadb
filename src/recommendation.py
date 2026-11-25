import json
from functools import cache

import numpy as np

MODEL_NAME = "BAAI/bge-m3"
RECOMMENDATION_COUNT = 3


@cache
def load_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def embed(texts):
    return load_model().encode(texts, normalize_embeddings=True)


def movie_text(title, year, genres, description):
    if genres:
        return f"{title} ({year}). {genres}. {description}"
    return f"{title} ({year}). {description}"


def movie_texts(conn):
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT
                m.id,
                m.title,
                YEAR(m.release_date) AS year,
                GROUP_CONCAT(g.name ORDER BY g.name SEPARATOR ', ') AS genres,
                m.description
            FROM movie m
            LEFT JOIN movie_genre mg ON mg.movie_id = m.id
            LEFT JOIN genre g ON g.id = mg.genre_id
            GROUP BY m.id
            ORDER BY m.id
            """
        )
        movies = cursor.fetchall()
    return {
        movie["id"]: movie_text(
            movie["title"], movie["year"], movie["genres"], movie["description"]
        )
        for movie in movies
    }


def embed_movies(conn):
    texts = movie_texts(conn)
    embeddings = embed(list(texts.values()))
    rows = [
        (movie_id, json.dumps(embedding.tolist()))
        for movie_id, embedding in zip(texts, embeddings, strict=True)
    ]
    with conn.cursor() as cursor:
        conn.start_transaction()
        try:
            cursor.execute("DELETE FROM movie_embedding")
            cursor.executemany(
                """
                INSERT INTO movie_embedding (movie_id, embedding)
                VALUES (%s, STRING_TO_VECTOR(%s))
                """,
                rows,
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return len(rows)


def recommend(conn, description):
    description = description.strip()
    if not description:
        raise ValueError("Please describe what you would like to watch.")
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT m.id, m.title, e.embedding
            FROM movie_embedding e
            JOIN movie m ON m.id = e.movie_id
            ORDER BY m.id
            """
        )
        movies = cursor.fetchall()
    if not movies:
        raise ValueError("No movie embeddings found. Run `cinema embed` first.")
    movie_embeddings = np.array([movie["embedding"] for movie in movies], dtype=np.float32)
    cosine_similarities = movie_embeddings @ embed([description])[0]
    best = np.argsort(-cosine_similarities, kind="stable")[:RECOMMENDATION_COUNT]
    return [
        {
            "id": movies[index]["id"],
            "title": movies[index]["title"],
            "similarity": float(cosine_similarities[index]),
        }
        for index in best
    ]
