import pandas as pd

from common import MOVIES_PATH, RAW_MOVIES_PATH

REQUIRED_COLUMNS = ["title", "overview", "genres", "release_date"]


def load_raw_movies() -> pd.DataFrame:
    return pd.read_csv(
        RAW_MOVIES_PATH,
        usecols=["id", *REQUIRED_COLUMNS],
        keep_default_na=False,
        dtype={"id": "int64", **dict.fromkeys(REQUIRED_COLUMNS, "str")},
    )


def strip_whitespace(movies: pd.DataFrame) -> pd.DataFrame:
    return movies.assign(**{column: movies[column].str.strip() for column in REQUIRED_COLUMNS})


def to_schema_shape(movies: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": movies["id"],
            "title": movies["title"],
            "year": movies["release_date"].str[:4].astype("int64"),
            "genres": movies["genres"].str.replace("-", ", ", regex=False),
            "overview": movies["overview"],
        }
    )


def main() -> None:
    movies = load_raw_movies()
    print(f"Rows in {RAW_MOVIES_PATH.name}: {len(movies):,}")
    movies = movies.drop_duplicates(subset="id", keep="first")
    print(f"After dropping repeated ids: {len(movies):,}")
    movies = strip_whitespace(movies)
    for column in REQUIRED_COLUMNS:
        movies = movies[movies[column] != ""]
        print(f"After dropping empty {column}: {len(movies):,}")
    clean_movies = to_schema_shape(movies)
    clean_movies.to_csv(MOVIES_PATH, index=False)
    print(f"Wrote {len(clean_movies):,} movies to {MOVIES_PATH}")


if __name__ == "__main__":
    main()
