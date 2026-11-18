"""Evaluate saved movie/query vectors with cosine similarity, Recall@3 and full-rank MRR."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import issparse, load_npz

PIPELINE_DIR = Path(__file__).resolve().parent
DATA_DIR = PIPELINE_DIR / "data"
RESULTS_DIR = PIPELINE_DIR / "results"
MODELS = [
    "TF-IDF",
    "paraphrase-multilingual-MiniLM-L12-v2",
    "paraphrase-multilingual-mpnet-base-v2",
    "intfloat/multilingual-e5-small",
    "intfloat/multilingual-e5-base",
    "BAAI/bge-m3",
]
LANGUAGES = ["en", "it"]
TOP_K = 3
QUERY_BATCH_SIZE = 8


def row_norms(vectors):
    """Calculate lengths in blocks, without copying a full dense movie matrix."""
    if vectors.ndim != 2:
        raise ValueError("Vectors must be a two-dimensional matrix.")
    norms = np.empty(vectors.shape[0], dtype=np.float64)
    for start in range(0, vectors.shape[0], 16384):
        block = vectors[start:start + 16384]
        if issparse(block):
            squared_lengths = np.asarray(block.multiply(block).sum(axis=1)).ravel()
        else:
            squared_lengths = np.einsum("ij,ij->i", block, block)
        norms[start:start + len(squared_lengths)] = np.sqrt(squared_lengths)
    if not np.isfinite(norms).all():
        raise ValueError("Vectors contain non-finite values.")
    return norms


def top_indices(scores, movie_ids, k=TOP_K):
    """Select top scores; tied scores are ordered by ascending movie ID."""
    k = min(k, len(scores))
    threshold = np.partition(scores, len(scores) - k)[len(scores) - k]
    above = np.flatnonzero(scores > threshold)
    tied = np.flatnonzero(scores == threshold)
    remaining = k - len(above)
    if len(tied) > remaining:
        selected = np.argpartition(movie_ids[tied], remaining - 1)[:remaining]
        tied = tied[selected]
    selected = np.concatenate([above, tied])
    order = np.lexsort((movie_ids[selected], -scores[selected]))
    return selected[order]


def query_metrics(scores, movie_ids, relevant_positions):
    """Return Recall@3 and the reciprocal rank of the first relevant movie."""
    top = top_indices(scores, movie_ids)
    hits = np.isin(top, relevant_positions).sum()
    recall = float(hits / len(relevant_positions))

    # MRR uses the full ranking, including relevant movies below position three.
    relevant_scores = scores[relevant_positions]
    best_score = relevant_scores.max()
    best_ids = movie_ids[relevant_positions[relevant_scores == best_score]]
    best_id = best_ids.min()
    ahead = (scores > best_score) | ((scores == best_score) & (movie_ids < best_id))
    first_rank = int(np.count_nonzero(ahead)) + 1
    return recall, 1.0 / first_rank, first_rank, top


def evaluate_vectors(movie_vectors, query_vectors, movie_ids, query_ids,
                     relevant_positions, ground_truth, movie_norms,
                     batch_size=QUERY_BATCH_SIZE):
    """Score query batches against the entire corpus, keeping memory bounded."""
    if movie_vectors.shape[0] != len(movie_ids):
        raise ValueError("Movie vector rows do not match movie_ids.npy.")
    if query_vectors.shape[0] != len(query_ids):
        raise ValueError("Query vector rows do not match the saved query IDs.")
    if movie_vectors.shape[1] != query_vectors.shape[1]:
        raise ValueError("Movie and query vector dimensions differ.")
    query_lengths = row_norms(query_vectors)
    movie_lengths = np.where(movie_norms == 0, 1.0, movie_norms)
    for start in range(0, len(query_ids), batch_size):
        batch = query_vectors[start:start + batch_size]
        products = batch @ movie_vectors.T
        scores = products.toarray() if issparse(products) else np.asarray(products)
        lengths = query_lengths[start:start + len(scores)]
        scores /= np.where(lengths == 0, 1.0, lengths)[:, None]
        scores /= movie_lengths[None, :]
        for offset, query_scores in enumerate(scores):
            query_id = query_ids[start + offset]
            positions = relevant_positions[query_id]
            recall, reciprocal_rank, first_rank, top = query_metrics(
                query_scores, movie_ids, positions,
            )
            yield {
                "query_id": query_id,
                "query_type": ground_truth[query_id]["query_type"],
                "relevant_movie_count": len(positions),
                "recall_at_3": recall,
                "reciprocal_rank": reciprocal_rank,
                "first_relevant_rank": first_rank,
                "zero_query_vector": bool(query_lengths[start + offset] == 0),
                "top_3_movie_ids": json.dumps(movie_ids[top].tolist()),
                "top_3_cosine_scores": json.dumps(query_scores[top].tolist()),
            }


def evaluate(data_dir=DATA_DIR, results_dir=RESULTS_DIR):
    with (data_dir / "ground_truth.json").open(encoding="utf-8") as source:
        ground_truth = json.load(source)
    embedding_dir = data_dir / "title_genres_keywords_production_companies"
    movie_ids = np.load(embedding_dir / "movie_ids.npy", allow_pickle=False)
    if movie_ids.ndim != 1 or len(movie_ids) == 0:
        raise ValueError("Movie IDs must be a nonempty list.")
    if len(np.unique(movie_ids)) != len(movie_ids):
        raise ValueError("Duplicated movie IDs.")
    movie_positions = {int(movie_id): position for position, movie_id in enumerate(movie_ids)}
    relevant_positions = {}
    for query_id, labels in ground_truth.items():
        relevant_ids = {int(movie["movie_id"]) for movie in labels["relevant_movies"]}
        missing = relevant_ids.difference(movie_positions)
        if not relevant_ids or missing:
            raise ValueError(f"{query_id}: empty labels or relevant IDs missing from corpus.")
        relevant_positions[query_id] = np.array(
            [movie_positions[movie_id] for movie_id in relevant_ids], dtype=np.int64,
        )

    query_ids_by_language = {}
    for language in LANGUAGES:
        ids = np.load(embedding_dir / f"query_ids_{language}.npy", allow_pickle=False)
        ids = ids.astype(str).tolist()
        if len(set(ids)) != len(ids) or set(ids) != set(ground_truth):
            raise ValueError(f"{language}: saved query IDs do not match ground truth.")
        query_ids_by_language[language] = ids

    records = []
    for model in MODELS:
        safe_model = model.replace("/", "_")
        if model == "TF-IDF":
            movie_path = embedding_dir / "tfidf_vectors.npz"
            query_paths = {
                language: embedding_dir / f"query_tfidf_vectors_{language}.npz"
                for language in LANGUAGES
            }
        else:
            movie_path = embedding_dir / f"embeddings_{safe_model}.npy"
            query_paths = {
                language: embedding_dir / f"query_embeddings_{safe_model}_{language}.npy"
                for language in LANGUAGES
            }
        movie_vectors = (
            load_npz(movie_path).tocsr() if model == "TF-IDF"
            else np.load(movie_path, mmap_mode="r", allow_pickle=False)
        )
        movie_norms = row_norms(movie_vectors)
        for language, query_path in query_paths.items():
            query_vectors = (
                load_npz(query_path).tocsr() if model == "TF-IDF"
                else np.load(query_path, mmap_mode="r", allow_pickle=False)
            )
            for result in evaluate_vectors(
                movie_vectors, query_vectors, movie_ids, query_ids_by_language[language],
                relevant_positions, ground_truth, movie_norms,
            ):
                records.append({"model": model, "language": language, **result})
            del query_vectors
        del movie_vectors, movie_norms

    per_query = pd.DataFrame(records)
    summary = per_query.groupby(["model", "language"], as_index=False).agg(
        recall_at_3=("recall_at_3", "mean"),
        mrr=("reciprocal_rank", "mean"),
    )
    table = summary.pivot(index="model", columns="language", values=["recall_at_3", "mrr"])
    table = table.loc[:, [("recall_at_3", "en"), ("mrr", "en"),
                          ("recall_at_3", "it"), ("mrr", "it")]]
    table.columns = ["Recall@3 (EN)", "MRR (EN)", "Recall@3 (IT)", "MRR (IT)"]
    table = table.reset_index().rename(columns={"model": "Model"})
    results_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(results_dir / "comparison_table.csv", index=False, float_format="%.8f")


if __name__ == "__main__":
    evaluate()
