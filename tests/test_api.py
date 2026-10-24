"""Тесты API мини-сервисдеска. Запускаются pytest'ом против локального PostgreSQL.

Фикстура client подключается автоматически из conftest.py.
"""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_create_ticket(client):
    resp = client.post(
        "/tickets",
        json={"title": "Не работает оплата", "description": "Ошибка при оплате"},
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["id"] == 1
    assert data["title"] == "Не работает оплата"
    assert data["status"] == "open"


def test_create_ticket_without_title(client):
    resp = client.post("/tickets", json={"description": "без заголовка"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_list_tickets_and_filter_by_status(client):
    client.post("/tickets", json={"title": "первый"})
    client.post("/tickets", json={"title": "второй"})
    client.patch("/tickets/1", json={"status": "resolved"})

    all_tickets = client.get("/tickets").get_json()
    assert len(all_tickets) == 2

    resolved = client.get("/tickets?status=resolved").get_json()
    assert [t["id"] for t in resolved] == [1]


def test_change_status(client):
    client.post("/tickets", json={"title": "тикет"})
    resp = client.patch("/tickets/1", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "in_progress"


def test_change_status_invalid_value(client):
    client.post("/tickets", json={"title": "тикет"})
    resp = client.patch("/tickets/1", json={"status": "closed"})
    assert resp.status_code == 400


def test_missing_ticket_404(client):
    assert client.get("/tickets/999").status_code == 404


def test_comments(client):
    client.post("/tickets", json={"title": "тикет"})
    resp = client.post(
        "/tickets/1/comments",
        json={"author": "agent", "body": "Проблема в работе, чиним"},
    )
    assert resp.status_code == 201

    data = client.get("/tickets/1").get_json()
    assert len(data["comments"]) == 1
    assert data["comments"][0]["body"] == "Проблема в работе, чиним"


def test_comment_without_body(client):
    client.post("/tickets", json={"title": "тикет"})
    resp = client.post("/tickets/1/comments", json={})
    assert resp.status_code == 400
