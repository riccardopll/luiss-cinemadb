# Embedding model selection

The app recommends three movies for a client's free-text interest description. It embeds the description and every movie's text, then ranks the movies by cosine similarity. This folder is an offline experiment that picks the embedding model the app uses, by testing candidate methods on a public movie dataset shaped like our `movie` table.

## Corpus

`data/movies.csv` has 722,317 rows. `01_prepare_dataset.py` drops repeated ids (keeping the first row), then keeps the movies whose title, overview, genres and release date are all non-empty after trimming whitespace. These are the movies that could be a row in our schema. It writes `id, title, year, genres, overview` to `data/movies_clean.csv`.

## Movie text

Each movie is embedded and indexed as:

```
{title} ({year}). {genres joined with ", "}. {overview}
```

## Queries

`data/queries.json` holds 108 queries. Each has an English (`en`) and an Italian (`it`) text.

- `q001`–`q100`: topic queries, written as a cinema client's interest description, such as "I'd like a period romance set in nineteenth-century England."
- `q101`–`q108`: sequel queries, such as "What is the next movie after "Toy Story"?". Each also has the id and title of its one correct answer (`answer_id`, `answer_title`).

## Methods

1. TF-IDF: scikit-learn `TfidfVectorizer` with default settings.
2. BM25: the `bm25s` library, tokenized without stemming and without stopword removal, because the queries are in two languages.
3. `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
4. `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
5. `intfloat/multilingual-e5-small`
6. `intfloat/multilingual-e5-base`
7. `BAAI/bge-m3`

The two e5 models get the prefix `passage: ` on movie texts and `query: ` on queries, as their model cards require. All embeddings are L2-normalized, so cosine similarity is a dot product. Each method returns its top ten movies for every query in each language.

The movie texts are in English only. TF-IDF and BM25 match words, so on the Italian queries they score close to zero (nDCG@10 below 0.04). They would need the movie texts or the queries translated to work in Italian, which this experiment does not do. The embedding models compare meaning, so they rank English movie texts for an Italian query without translation.

## Answer key

The answer key in `data/judgements.json` was written once by Claude Sonnet 5.5. It read each movie's text and marked the movie relevant or not relevant for the query. The pool it judged is every movie that any method returned in its top ten for a topic query. `04_evaluate.py` only reads that file. Sequel queries are not in it: they are graded against their `answer_id`.

The judge did not read the whole corpus, so a relevant movie that no method returned is not in the answer key. The scores compare these seven methods fairly, because every movie they returned has a verdict. nDCG@10 is not an absolute measure: its ideal ranking counts only the relevant movies that were found, so the real ceiling can be higher. A method added later returns movies that have no verdict, and they must be judged before `04_evaluate.py` can grade it.

## Scores

Each score is averaged over all 108 queries, per method and language.

- nDCG@10, with binary relevance. The ideal ranking puts the query's known relevant movies first: for a topic query, the movies judged relevant for it; for a sequel query, its one answer. A topic query with no relevant movie scores 0.
- Precision@3: the share of the top three that is relevant.
- MRR@10: 1 / rank of the first relevant movie in the top ten, or 0 if there is none.

The recommended model is the embedding model with the highest nDCG@10, averaged equally over English and Italian. Precision@3, the score closest to the three movies the app shows, ranks the five embedding models in the same order.

## How to run

From the repository root:

```
uv run python pipeline/01_prepare_dataset.py
uv run python pipeline/02_embed.py
uv run python pipeline/03_retrieve.py
uv run python pipeline/04_evaluate.py
uv run jupyter nbconvert --to notebook --execute --inplace pipeline/report.ipynb
```
