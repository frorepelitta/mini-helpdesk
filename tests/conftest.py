"""Подготовка окружения для тестов: чистая база + тестовый клиент Flask."""
import psycopg2
import pytest

from app import DATABASE_URL, app, init_db


@pytest.fixture()
def client():
    """Тестовый клиент: перед каждым тестом таблицы пересоздаются пустыми."""
    init_db()
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn, conn.cursor() as cur:
            cur.execute("TRUNCATE comments, tickets RESTART IDENTITY CASCADE")
    finally:
        conn.close()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client
