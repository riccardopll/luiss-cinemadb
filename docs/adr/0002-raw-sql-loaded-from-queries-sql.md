# Raw SQL loaded by name from queries.sql, no ORM

Every group member must be able to explain the SQL, the parameter passing and the `SELECT ... FOR UPDATE` booking transaction live. An ORM would hide exactly those things. We use `mysql-connector-python` (the course library) with parameterized SQL, and every statement the app runs lives in `queries.sql` under a `-- name: <query_name>` line that `cinema.database` loads. The graded queries and the queries the app runs therefore cannot drift apart.
