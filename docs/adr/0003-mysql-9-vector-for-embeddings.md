# MySQL 9 with the VECTOR type stores movie embeddings

Movie embeddings are stored in MySQL in a `VECTOR` column, keyed by movie, embedding model and a hash of the movie text, so they are part of the database design rather than a side file. `VECTOR` needs MySQL >= 9.0, while the course does not pin a version and MySQL 8.4 would also have worked with a JSON column. We accept the MySQL 9 requirement and make it easy to meet with the `mysql:9.7` Docker image. Similarity is computed in Python, because `DISTANCE()` is only available on HeatWave.
