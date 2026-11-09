import bcrypt


def login(conn, email, password):
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT u.id, u.password_hash, u.role, c.name
            FROM user u
            LEFT JOIN client c ON c.user_id = u.id
            WHERE u.email = %s
            """,
            (email,),
        )
        user = cursor.fetchone()
    if user is None or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return None
    return {"id": user["id"], "role": user["role"], "name": user["name"]}
