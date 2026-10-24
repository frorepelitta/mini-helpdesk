# Mini HelpDesk

[![CI](https://github.com/frorepelitta/mini-helpdesk/actions/workflows/ci.yml/badge.svg)](https://github.com/frorepelitta/mini-helpdesk/actions/workflows/ci.yml)

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
- **Kubernetes** — деплой приложения в кластер (Deployment, Service, Ingress)
- **GitHub Actions** — CI: линт, автотесты, сборка docker-образа

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

## Kubernetes

Приложение деплоится в кластер Kubernetes (манифесты в папке `k8s/`).

**Как запустить** (Kubernetes из Docker Desktop: Settings → Kubernetes → Enable):

```bash
docker compose build              # собрать образ, он виден кластеру

# ingress-контроллер (один раз)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.12.1/deploy/static/provider/cloud/deploy.yaml

kubectl apply -f k8s/             # база + api + ingress
```

API станет доступен на http://localhost (порт 80, через ingress-nginx).

**Что в манифестах:**

- `secret.yml` — параметры подключения к БД (в реальности — Vault/Sealed Secrets)
- `postgres.yml` — база: PersistentVolumeClaim + Deployment + Service
- `api.yml` — API: Deployment на 2 пода + Service, readiness/liveness пробы на `/health`
- `ingress.yml` — входящий трафик → сервис api

**Полезные команды:**

```bash
kubectl get pods                  # статус подов
kubectl scale deployment api --replicas=3   # масштабирование без даунтайма
kubectl logs -l app=api           # логи приложения
kubectl delete pod <имя-пода>     # удалить под — Kubernetes сам создаст новый,
                                  # трафик при этом не падает
```

## CI (GitHub Actions)

При каждом пуше и pull request'е автоматически запускается пайплайн (`.github/workflows/ci.yml`):

1. **Линт** — flake8 проверяет код
2. **Тесты** — pytest гоняет 9 тестов против PostgreSQL,
   который поднимается отдельным service-контейнером
3. **Сборка** — docker-образ приложения собирается (пушится только если тесты прошли)

Локально тесты запускаются так (нужен любой PostgreSQL, доступный по DATABASE_URL):

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt -r requirements-dev.txt   # Linux: .venv/bin/pip
.venv/Scripts/python -m pytest -v
```

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
k8s/
  secret.yml             — параметры БД (Secret)
  postgres.yml           — база: PVC + Deployment + Service
  api.yml                — API: Deployment (2 пода, пробы) + Service
  ingress.yml            — входящий трафик → api
tests/
  conftest.py            — фикстура pytest: чистая база + тестовый клиент
  test_api.py            — тесты всех эндпоинтов
requirements-dev.txt     — зависимости для разработки (pytest, flake8)
setup.cfg                — настройка flake8
.github/workflows/ci.yml — пайплайн CI
```

## План развития

- [ ] nginx как reverse proxy
- [x] Мониторинг: Prometheus + Grafana
- [x] Kubernetes (Deployment, Service, Ingress)
- [x] CI/CD: GitHub Actions (линт, тесты, сборка образа)
- [ ] LLM-ассистент: «предложить ответ агенту»
