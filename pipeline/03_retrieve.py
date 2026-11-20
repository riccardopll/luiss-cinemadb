import bm25s
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from common import (
    EMBEDDING_MODELS,
    LANGUAGES,
    QUERIES_PATH,
    RANKINGS_PATH,
    RESULTS_DIR,
    TOP_K,
    embedding_path,
    is_sequel,
    load_json,
    load_movies,
    movie_texts,
)


def check_sequel_answers(queries: dict, movie_ids: np.ndarray) -> None:
    missing = [
        f"{query_id} (answer_id {query['answer_id']})"
        for query_id, query in queries.items()
        if is_sequel(query) and query["answer_id"] not in movie_ids
    ]
    if missing:
        raise ValueError(f"Sequel answers missing from movies_clean.csv: {', '.join(missing)}")


def top_k(scores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    candidates = np.argpartition(-scores, TOP_K, axis=1)[:, :TOP_K]
    candidate_scores = np.take_along_axis(scores, candidates, axis=1)
    order = np.argsort(-candidate_scores, axis=1, kind="stable")
    indices = np.take_along_axis(candidates, order, axis=1)
    return indices, np.take_along_axis(candidate_scores, order, axis=1)


def ranking_rows(
    method: str,
    language: str,
    query_ids: list[str],
    indices: np.ndarray,
    scores: np.ndarray,
    movie_ids: np.ndarray,
) -> list[dict]:
    return [
        {
            "method": method,
            "language": language,
            "query_id": query_id,
            "rank": rank,
            "movie_id": int(movie_ids[index]),
            "score": float(score),
        }
        for query_id, query_indices, query_scores in zip(query_ids, indices, scores, strict=True)
        for rank, (index, score) in enumerate(zip(query_indices, query_scores, strict=True), 1)
    ]


def rank_tfidf(texts: list[str], queries: dict, movie_ids: np.ndarray) -> list[dict]:
    vectorizer = TfidfVectorizer()
    movie_matrix = vectorizer.fit_transform(texts)
    rows = []
    for language in LANGUAGES:
        query_matrix = vectorizer.transform([query[language] for query in queries.values()])
        scores = (query_matrix @ movie_matrix.T).toarray()
        rows += ranking_rows("TF-IDF", language, list(queries), *top_k(scores), movie_ids)
    return rows


def rank_bm25(texts: list[str], queries: dict, movie_ids: np.ndarray) -> list[dict]:
    retriever = bm25s.BM25()
    retriever.index(bm25s.tokenize(texts, stopwords=None, show_progress=False), show_progress=False)
    rows = []
    for language in LANGUAGES:
        query_tokens = bm25s.tokenize(
            [query[language] for query in queries.values()],
            stopwords=None,
            return_ids=False,
            show_progress=False,
        )
        indices, scores = retriever.retrieve(query_tokens, k=TOP_K, show_progress=False)
        rows += ranking_rows("BM25", language, list(queries), indices, scores, movie_ids)
    return rows


def load_movie_embeddings(model_name: str, movie_count: int) -> np.ndarray:
    path = embedding_path(model_name, "movies")
    matrix = np.load(path)
    if matrix.shape[0] != movie_count:
        raise ValueError(
            f"{path.name} has {matrix.shape[0]:,} rows but movies_clean.csv has "
            f"{movie_count:,} movies. Delete it and run 02_embed.py again."
        )
    return matrix


def rank_embeddings(model_name: str, queries: dict, movie_ids: np.ndarray) -> list[dict]:
    movie_matrix = load_movie_embeddings(model_name, len(movie_ids))
    rows = []
    for language in LANGUAGES:
        query_matrix = np.load(embedding_path(model_name, f"queries_{language}"))
        scores = query_matrix @ movie_matrix.T
        rows += ranking_rows(model_name, language, list(queries), *top_k(scores), movie_ids)
    return rows


def main() -> None:
    movies = load_movies()
    movie_ids = movies["id"].to_numpy()
    queries = load_json(QUERIES_PATH)
    check_sequel_answers(queries, movie_ids)
    texts = movie_texts(movies)

    print("Ranking with TF-IDF")
    rows = rank_tfidf(texts, queries, movie_ids)
    print("Ranking with BM25")
    rows += rank_bm25(texts, queries, movie_ids)
    for model_name in EMBEDDING_MODELS:
        print(f"Ranking with {model_name}")
        rows += rank_embeddings(model_name, queries, movie_ids)

    RESULTS_DIR.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(RANKINGS_PATH, index=False)
    print(f"Wrote {len(rows):,} rows to {RANKINGS_PATH}")


if __name__ == "__main__":
    main()
