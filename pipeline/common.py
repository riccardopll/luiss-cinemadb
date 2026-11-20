import json
from pathlib import Path

import pandas as pd

PIPELINE_DIR = Path(__file__).resolve().parent
DATA_DIR = PIPELINE_DIR / "data"
RESULTS_DIR = PIPELINE_DIR / "results"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"

RAW_MOVIES_PATH = DATA_DIR / "movies.csv"
MOVIES_PATH = DATA_DIR / "movies_clean.csv"
QUERIES_PATH = DATA_DIR / "queries.json"
JUDGEMENTS_PATH = DATA_DIR / "judgements.json"
RANKINGS_PATH = RESULTS_DIR / "rankings.csv"
PER_QUERY_PATH = RESULTS_DIR / "per_query.csv"
SUMMARY_PATH = RESULTS_DIR / "summary.csv"

EMBEDDING_MODELS = [
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    "intfloat/multilingual-e5-small",
    "intfloat/multilingual-e5-base",
    "BAAI/bge-m3",
]
LANGUAGES = ["en", "it"]
TOP_K = 10


def load_movies() -> pd.DataFrame:
    return pd.read_csv(
        MOVIES_PATH,
        keep_default_na=False,
        dtype={"id": "int64", "title": "str", "year": "int64", "genres": "str", "overview": "str"},
    )


def movie_text(title: str, year: int, genres: str, overview: str) -> str:
    return f"{title} ({year}). {genres}. {overview}"


def movie_texts(movies: pd.DataFrame) -> list[str]:
    return [
        movie_text(title, year, genres, overview)
        for title, year, genres, overview in zip(
            movies["title"], movies["year"], movies["genres"], movies["overview"], strict=True
        )
    ]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def is_sequel(query: dict) -> bool:
    return "answer_id" in query


def embedding_path(model_name: str, part: str) -> Path:
    return EMBEDDINGS_DIR / f"{model_name.split('/')[-1]}_{part}.npy"
