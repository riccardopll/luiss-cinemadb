import numpy as np
import pandas as pd

from common import (
    JUDGEMENTS_PATH,
    PER_QUERY_PATH,
    QUERIES_PATH,
    RANKINGS_PATH,
    SUMMARY_PATH,
    TOP_K,
    is_sequel,
    load_json,
)

SCORE_COLUMNS = ["ndcg_at_10", "precision_at_3", "mrr_at_10"]
DISCOUNTS = 1 / np.log2(np.arange(2, TOP_K + 2))


def relevant_ids_by_query(queries: dict, judgements: dict) -> dict[str, set[int]]:
    return {
        query_id: {query["answer_id"]}
        if is_sequel(query)
        else set(judgements[query_id]["relevant"])
        for query_id, query in queries.items()
    }


def check_judgements(rankings: pd.DataFrame, queries: dict, judgements: dict) -> None:
    topic_ids = [query_id for query_id, query in queries.items() if not is_sequel(query)]
    topic_rankings = rankings[rankings["query_id"].isin(topic_ids)]
    judged = {
        (query_id, movie_id)
        for query_id, verdicts in judgements.items()
        for movie_id in verdicts["relevant"] + verdicts["not_relevant"]
    }
    pairs = set(zip(topic_rankings["query_id"], topic_rankings["movie_id"], strict=True))
    unjudged = pairs - judged
    if unjudged:
        raise ValueError(
            f"{len(unjudged):,} ranked (query, movie) pairs of topic queries have no verdict "
            f"in {JUDGEMENTS_PATH.name}."
        )


def query_scores(ranked_ids: list[int], relevant_ids: set[int]) -> dict[str, float]:
    hits = np.array([movie_id in relevant_ids for movie_id in ranked_ids], dtype=float)
    ideal = DISCOUNTS[: min(len(relevant_ids), TOP_K)].sum()
    first_hit = np.flatnonzero(hits)
    return {
        "ndcg_at_10": float(hits @ DISCOUNTS / ideal) if ideal else 0.0,
        "precision_at_3": float(hits[:3].mean()),
        "mrr_at_10": float(1 / (first_hit[0] + 1)) if first_hit.size else 0.0,
    }


def score_rankings(rankings: pd.DataFrame, queries: dict, judgements: dict) -> pd.DataFrame:
    relevant_ids = relevant_ids_by_query(queries, judgements)
    rows = []
    for (method, language, query_id), ranking in rankings.groupby(
        ["method", "language", "query_id"], sort=False
    ):
        ranked_ids = ranking.sort_values("rank")["movie_id"].tolist()
        rows.append(
            {
                "method": method,
                "language": language,
                "query_id": query_id,
                "query_type": "sequel" if is_sequel(queries[query_id]) else "topic",
                **query_scores(ranked_ids, relevant_ids[query_id]),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    rankings = pd.read_csv(RANKINGS_PATH)
    queries = load_json(QUERIES_PATH)
    judgements = load_json(JUDGEMENTS_PATH)
    check_judgements(rankings, queries, judgements)

    per_query = score_rankings(rankings, queries, judgements)
    summary = per_query.groupby(["method", "language"], sort=False, as_index=False)[
        SCORE_COLUMNS
    ].mean()
    per_query.to_csv(PER_QUERY_PATH, index=False)
    summary.to_csv(SUMMARY_PATH, index=False)
    print(f"Wrote {PER_QUERY_PATH} and {SUMMARY_PATH}")
    print(summary.to_string(index=False, float_format="%.3f"))


if __name__ == "__main__":
    main()
