# MySQL 9 with the VECTOR type stores movie embeddings

Movie embeddings are stored in MySQL in a `VECTOR` column, so they are part of the database design rather than a side file. `VECTOR` needs MySQL >= 9.0, while the course does not pin a version and MySQL 8.4 would also have worked with a JSON column. We accept the MySQL 9 requirement and make it easy to meet with the `mysql:9.7` Docker image. Similarity is computed in Python, because `DISTANCE()` is only available on HeatWave.

The vectors live in their own table, `movie_embedding(movie_id, embedding)`, rather than as a column on `movie`, so the ordinary movie and screening queries never read them. Only the recommendation code joins it.

The table stores no model name or text hash, so the app cannot detect stale vectors. After re-seeding, changing movie data or changing the embedding model, `cinema embed` must be run to regenerate all embeddings.
