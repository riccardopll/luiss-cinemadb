# Embedding model selection

Shows which pretrained embedding model and which text template the app uses, and why.

1. `01_prepare_dataset.py`: download the public movie dataset into `data/raw/` and clean it.
2. `02_build_queries.py`: build English interest descriptions from genres and keywords, with their relevant movies.
3. `data/queries_it.*`: Italian translation of the queries, produced once with an LLM and committed.
4. `03_embed.py`: embed movies and queries with every candidate model and text template.
5. `04_evaluate.py`: compute Recall@3 and MRR, write tables to `results/`.
6. `report.ipynb`: tables and charts for the presentation.

Candidates: `paraphrase-multilingual-MiniLM-L12-v2`, `paraphrase-multilingual-mpnet-base-v2`, `intfloat/multilingual-e5-small`, `intfloat/multilingual-e5-base`, `BAAI/bge-m3`, and a TF-IDF baseline.

Run with `uv run python pipeline/<script>.py`. Results are committed, so rerunning is optional.
