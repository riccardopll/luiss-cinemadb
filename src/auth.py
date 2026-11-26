import bcrypt

BCRYPT_MAX_PASSWORD_BYTES = 72


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
    password_bytes = password.encode()
    if (
        user is None
        or len(password_bytes) > BCRYPT_MAX_PASSWORD_BYTES
        or not bcrypt.checkpw(password_bytes, user["password_hash"].encode())
    ):
        return None
    return {"id": user["id"], "role": user["role"], "name": user["name"]}
