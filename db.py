import os
from contextlib import contextmanager
from typing import Optional, List
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


@contextmanager
def get_conn():
    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(64) UNIQUE NOT NULL,
        password_hash VARCHAR(128) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS posts (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE
    );
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(schema)
        conn.commit()


def create_user(username: str, password_hash: str) -> Optional[int]:
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id;",
                    (username, password_hash),
                )
                user_id = cur.fetchone()[0]
            conn.commit()
        return user_id
    except Exception:
        return None


def get_user_by_username(username: str) -> Optional[tuple[int, str]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, password_hash FROM users WHERE username = %s;",
                (username,),
            )
            row = cur.fetchone()
    
    return row if row else None


def get_posts_by_user_id(user_id: int) -> List[tuple[int, str, str]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, body FROM posts WHERE owner_id = %s ORDER BY id;",
                (user_id,),
            )
            rows = cur.fetchall()
    
    return rows if rows else []


def create_post(title: str, body: str, owner_id: int) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO posts (title, body, owner_id) VALUES (%s, %s, %s) RETURNING id;",
                (title, body, owner_id),
            )
            post_id = cur.fetchone()[0]
        conn.commit()
    
    return post_id
