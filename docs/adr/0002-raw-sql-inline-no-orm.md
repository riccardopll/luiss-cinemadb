# Raw SQL written inline, no ORM; queries.sql holds only the five graded queries

Every group member must be able to explain the SQL, the parameter passing and the `SELECT ... FOR UPDATE` booking transaction live. An ORM would hide exactly those things. We use `mysql-connector-python` (the course library) and write parameterized SQL inline in `cursor.execute(...)`, as in the course's Python and MySQL lab.

`queries.sql` contains only the five queries the brief grades, so they are easy to find. There, parameters are MySQL session variables set by a `SET` line, so the file runs on its own in MySQL. The Python code runs the same queries with driver placeholders, and a change to one of them must be made in both places.
