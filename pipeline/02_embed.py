import numpy as np
from sentence_transformers import SentenceTransformer

from common import (
    EMBEDDING_MODELS,
    EMBEDDINGS_DIR,
    LANGUAGES,
    QUERIES_PATH,
    embedding_path,
    load_json,
    load_movies,
    movie_texts,
)

BATCH_SIZE = 64
E5_MOVIE_PREFIX = "passage: "
E5_QUERY_PREFIX = "query: "


def prefixes(model_name: str) -> tuple[str, str]:
    if model_name.startswith("intfloat/multilingual-e5"):
        return E5_MOVIE_PREFIX, E5_QUERY_PREFIX
    return "", ""


def texts_to_embed(model_name: str, movies: list[str], queries: dict) -> dict[str, list[str]]:
    movie_prefix, query_prefix = prefixes(model_name)
    texts = {"movies": [movie_prefix + text for text in movies]}
    for language in LANGUAGES:
        texts[f"queries_{language}"] = [
            query_prefix + query[language] for query in queries.values()
        ]
    return texts


def embed_model(model_name: str, texts: dict[str, list[str]]) -> None:
    missing_parts = [part for part in texts if not embedding_path(model_name, part).exists()]
    if not missing_parts:
        print(f"{model_name}: all embeddings exist, skipping")
        return
    model = SentenceTransformer(model_name)
    print(f"{model_name}: running on {model.device}")
    for part in missing_parts:
        print(f"{model_name}: embedding {len(texts[part]):,} texts for {part}")
        embeddings = model.encode(
            texts[part],
            batch_size=BATCH_SIZE,
            show_progress_bar=True,
            normalize_embeddings=True,
        )
        np.save(embedding_path(model_name, part), embeddings.astype(np.float32, copy=False))
    del model


def main() -> None:
    movies = movie_texts(load_movies())
    queries = load_json(QUERIES_PATH)
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    for model_name in EMBEDDING_MODELS:
        embed_model(model_name, texts_to_embed(model_name, movies, queries))


if __name__ == "__main__":
    main()
