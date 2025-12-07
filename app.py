import os
import html
from functools import wraps
from typing import Callable, Any

from flask import Flask, jsonify, request, g
from dotenv import load_dotenv

from db import init_db, create_user, get_user_by_username, get_posts_by_user_id, create_post as create_post_in_db, \
    drop_db
from security import hash_password, verify_password, create_access_token, decode_access_token

load_dotenv()

FLASK_HOST = os.getenv("FLASK_HOST")
FLASK_PORT = os.getenv("FLASK_PORT")
FLASK_DEBUG = bool(os.getenv("FLASK_DEBUG", "False"))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")


def login_required(fn: Callable) -> Callable:
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ", 1)[1].strip()
        payload = decode_access_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        g.current_user = {
            "id": int(payload["sub"]),
            "username": payload["username"],
        }
        return fn(*args, **kwargs)

    return wrapper


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    pw_hash = hash_password(password)

    user_id = create_user(username, pw_hash)
    if user_id is None:
        return jsonify({"error": "error during creating user"}), 409

    token = create_access_token(user_id, username)
    return jsonify({"token": token, "user": {"id": user_id, "username": username}}), 201

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    row = get_user_by_username(username)
    if not row:
        return jsonify({"error": "invalid credentials"}), 401

    user_id, password_hash = row
    if not verify_password(password, password_hash):
        return jsonify({"error": "invalid credentials"}), 401

    token = create_access_token(user_id, username)
    return jsonify({"token": token, "user": {"id": user_id, "username": username}})

@app.route("/api/data", methods=["GET"])
@login_required
def get_posts():
    user_id = g.current_user["id"]

    rows = get_posts_by_user_id(user_id)

    posts = [
        {
            "id": row[0],
            "title": html.escape(row[1]),
            "body": html.escape(row[2]),
        }
        for row in rows
    ]

    return jsonify({"items": posts})


@app.route("/api/data", methods=["POST"])
@login_required
def create_post():
    user_id = g.current_user["id"]
    data = request.get_json(force=True, silent=True) or {}
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()

    if not title or not body:
        return jsonify({"error": "title and body are required"}), 400

    post_id = create_post_in_db(title, body, user_id)

    return jsonify({"id": post_id, "title": html.escape(title), "body": html.escape(body)}), 201


if __name__ == "__main__":
    if FLASK_DEBUG == True:
        drop_db()
    init_db()
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
