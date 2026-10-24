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

## Запуск

Нужен установленный Docker:

```bash
docker compose up
```

Таблицы в базе создаются автоматически при первом запуске.
API поднимется на http://localhost:8000

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
docker-compose.yml   — api + postgres
```

## План развития

- [ ] nginx как reverse proxy
- [ ] Мониторинг: Prometheus + Grafana
- [ ] Kubernetes (Deployment, Service, Ingress)
- [ ] GitLab CI/CD: автотесты и автодеплой
- [ ] LLM-ассистент: «предложить ответ агенту»
