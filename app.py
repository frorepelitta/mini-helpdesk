"""Мини-сервисдеск: простой API для тикетов на Flask + PostgreSQL."""
import os
import time

import psycopg2
import psycopg2.extras
from flask import Flask, g, jsonify, request

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://helpdesk:helpdesk@localhost:5432/helpdesk",
)
ALLOWED_STATUSES = ("open", "in_progress", "resolved")

app = Flask(__name__)
# чтобы curl показывал кириллицу как текст, а не \u041d...
app.json.ensure_ascii = False


def get_db():
    """Соединение с БД на время одного запроса."""
    if "db" not in g:
        g.db = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(retries=15):
    """Создаёт таблицы, если их нет. Повторяет подключение, пока БД поднимается."""
    for attempt in range(retries):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            try:
                with conn, conn.cursor() as cur, open("schema.sql", encoding="utf-8") as f:
                    cur.execute(f.read())
            finally:
                conn.close()
            return
        except psycopg2.OperationalError:
            if attempt == retries - 1:
                raise
            time.sleep(2)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/tickets")
def list_tickets():
    status = request.args.get("status")
    with get_db().cursor() as cur:
        if status:
            cur.execute(
                "SELECT * FROM tickets WHERE status = %s ORDER BY created_at DESC",
                (status,),
            )
        else:
            cur.execute("SELECT * FROM tickets ORDER BY created_at DESC")
        return jsonify(cur.fetchall())


@app.post("/tickets")
def create_ticket():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    if not title:
        return jsonify({"error": "Поле 'title' обязательно"}), 400
    db = get_db()
    with db, db.cursor() as cur:
        cur.execute(
            "INSERT INTO tickets (title, description) VALUES (%s, %s) RETURNING *",
            (title, description),
        )
        ticket = cur.fetchone()
    return jsonify(ticket), 201


@app.get("/tickets/<int:ticket_id>")
def get_ticket(ticket_id):
    with get_db().cursor() as cur:
        cur.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
        ticket = cur.fetchone()
        if ticket is None:
            return jsonify({"error": "Тикет не найден"}), 404
        cur.execute(
            "SELECT * FROM comments WHERE ticket_id = %s ORDER BY created_at",
            (ticket_id,),
        )
        ticket["comments"] = cur.fetchall()
    return jsonify(ticket)


@app.patch("/tickets/<int:ticket_id>")
def change_status(ticket_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ALLOWED_STATUSES:
        return jsonify(
            {"error": "status должен быть одним из: " + ", ".join(ALLOWED_STATUSES)}
        ), 400
    db = get_db()
    with db, db.cursor() as cur:
        cur.execute(
            "UPDATE tickets SET status = %s WHERE id = %s RETURNING *",
            (status, ticket_id),
        )
        ticket = cur.fetchone()
        if ticket is None:
            return jsonify({"error": "Тикет не найден"}), 404
    return jsonify(ticket)


@app.post("/tickets/<int:ticket_id>/comments")
def add_comment(ticket_id):
    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"error": "Поле 'body' обязательно"}), 400
    db = get_db()
    with db, db.cursor() as cur:
        cur.execute("SELECT id FROM tickets WHERE id = %s", (ticket_id,))
        if cur.fetchone() is None:
            return jsonify({"error": "Тикет не найден"}), 404
        cur.execute(
            "INSERT INTO comments (ticket_id, author, body) VALUES (%s, %s, %s) RETURNING *",
            (ticket_id, (data.get("author") or "support").strip() or "support", body),
        )
        comment = cur.fetchone()
    return jsonify(comment), 201


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000)
