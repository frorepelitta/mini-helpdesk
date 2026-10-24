# Mini HelpDesk

Учебный пет-проект — простая система заявок (тикетов), как в сервис-деске.

## Что умеет API

| Метод | Путь | Что делает |
|---|---|---|
| GET | `/health` | Проверка, что сервис жив |
| GET | `/tickets` | Список тикетов, фильтр по статусу: `/tickets?status=open` |
| POST | `/tickets` | Создать тикет (`title`, `description`) |
| GET | `/tickets/<id>` | Один тикет + его комментарии |
| PATCH | `/tickets/<id>` | Сменить статус: `open` → `in_progress` → `resolved` |
| POST | `/tickets/<id>/comments` | Добавить комментарий (`author`, `body`) |

## Стек

- **Python 3 + Flask** — API
- **PostgreSQL** — хранение, обычные SQL-запросы без ORM
- **Docker Compose** — запуск одной командой (api + база)
- **Prometheus + Grafana** — метрики и дашборды

## Запуск

Нужен установленный Docker:

```bash
docker compose up
```

Таблицы в базе создаются автоматически при первом запуске.
API поднимется на http://localhost:8000

## Мониторинг

Поднимается вместе с приложением, отдельно настраивать ничего не нужно:

- **Grafana** — http://localhost:3000 (логин/пароль `admin`/`admin`),
  дашборд «Mini HelpDesk» подгружается автоматически:
  RPS по кодам ответа, время ответа p95, число запросов, живость API
- **Prometheus** — http://localhost:9090 (собирает метрики каждые 5 секунд)
- Метрики API в сыром виде — http://localhost:8000/metrics
- Метрики PostgreSQL собирает postgres-exporter

## Примеры запросов

```bash
# создать тикет
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{"title": "Не работает оплата", "description": "Ошибка при оплате картой"}'

# список тикетов
curl http://localhost:8000/tickets

# только открытые
curl "http://localhost:8000/tickets?status=open"

# сменить статус тикета №1
curl -X PATCH http://localhost:8000/tickets/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# добавить комментарий
curl -X POST http://localhost:8000/tickets/1/comments \
  -H "Content-Type: application/json" \
  -d '{"author": "agent", "body": "Проблема в работе, чиним"}'
```

> Нюанс Windows: если Git Bash ломает кириллицу в `-d '...'`, сохрани JSON в файл
> (например, `ticket.json`) и отправь его: `curl -X POST http://localhost:8000/tickets
> -H "Content-Type: application/json" --data-binary @ticket.json`

## Структура проекта

```
app.py               — всё приложение: роуты и SQL-запросы
schema.sql           — создание таблиц (выполняется при старте)
requirements.txt     — зависимости Python
Dockerfile           — образ для api
docker-compose.yml   — api + postgres + prometheus + grafana
monitoring/
  prometheus/prometheus.yml          — что и откуда собирать
  grafana/provisioning/              — автоподключение источника данных и дашборда
  grafana/dashboards/mini-helpdesk.json
```

## План развития

- [ ] nginx как reverse proxy
- [x] Мониторинг: Prometheus + Grafana
- [ ] Kubernetes (Deployment, Service, Ingress)
- [ ] GitLab CI/CD: автотесты и автодеплой
- [ ] LLM-ассистент: «предложить ответ агенту»
