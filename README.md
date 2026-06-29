# Collab Whiteboard

Курсовой проект по дисциплине «Проектирование и разработка клиент-серверных приложений»: интерактивная доска для совместной работы в реальном времени.

## Стек

- Backend: FastAPI, SQLAlchemy Async, Alembic, PostgreSQL.
- Frontend: React, TypeScript, Vite, production build через nginx.
- Auth: JWT access token, bcrypt-хеширование паролей.
- Realtime: WebSocket-каналы FastAPI.
- DevOps: Docker Compose, отдельный release-сервис миграций, healthcheck-и.
- Тестирование: pytest, httpx, Schemathesis fuzzing.

## Быстрый запуск

```bash
cp .env.example .env
docker compose up --build
```

После запуска:

- Frontend: `http://localhost:8080`
- Backend health: `http://localhost:8000/api/health`
- Swagger/OpenAPI: `http://localhost:8000/api/docs`

## Миграции и seed

Миграции запускаются отдельным сервисом `migrate` внутри Docker Compose. Seed-данные не выполняются автоматически при обычном старте API.

```bash
docker compose run --rm backend python -m app.seed
```

Демо-пользователи после seed:

| Роль | Email | Пароль |
|---|---|---|
| admin | `admin@example.com` | `Admin12345` |
| user | `demo@example.com` | `Demo12345` |
| user | `teammate@example.com` | `Demo12345` |

## Переменные окружения

См. `.env.example`. В production обязательно заменить `SECRET_KEY`, задать `ENV=production`, настроить `CORS_ORIGINS` и `DATABASE_URL`.

## Основные endpoint-ы

| Метод | Путь | Назначение | Auth |
|---|---|---|---|
| GET | `/api/health` | Healthcheck | нет |
| POST | `/api/auth/register` | Регистрация | нет |
| POST | `/api/auth/login` | JWT login | нет |
| GET | `/api/auth/me` | Текущий пользователь | да |
| GET/POST | `/api/workspaces` | Список/создание пространств | да |
| GET/PATCH/DELETE | `/api/workspaces/{id}` | CRUD пространства | да, owner/admin |
| GET/POST | `/api/boards` | Список/создание досок | да |
| GET/PATCH/DELETE | `/api/boards/{id}` | CRUD доски | да, board access |
| GET/POST | `/api/boards/{id}/elements` | CRUD элементов доски | да, editor+ |
| PATCH/DELETE | `/api/boards/{id}/elements/{element_id}` | Изменение/удаление элемента | да, editor+ |
| GET/POST | `/api/boards/{id}/comments` | Комментарии | да |
| GET | `/api/admin/users` | Пользователи | admin |
| WebSocket | `/api/ws/boards/{id}` | Realtime-события доски | token |

## Тестирование

Обычные backend-тесты:

```bash
cd backend
pytest
```

Фаззинг REST API через OpenAPI выполняется Schemathesis. FastAPI отдаёт OpenAPI 3.1, поэтому в скрипт уже добавлен флаг `--experimental=openapi-3.1`.

PowerShell-команды для запуска через Docker Compose:

```powershell
$LOGIN_RESPONSE = curl.exe -s -X POST "http://localhost:8000/api/auth/login" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=demo@example.com&password=Demo12345"

$TOKEN = ($LOGIN_RESPONSE | ConvertFrom-Json).access_token

docker compose exec -e BASE_URL=http://localhost:8000 -e TOKEN="$TOKEN" -e EXAMPLES=100 backend sh -lc "sh ./fuzz/run_fuzzing.sh"
```

Linux/macOS-команды:

```bash
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo@example.com&password=Demo12345")
TOKEN=$(python -c "import json,sys; print(json.load(sys.stdin)['access_token'])" <<< "$LOGIN_RESPONSE")
docker compose exec -e BASE_URL=http://localhost:8000 -e TOKEN="$TOKEN" -e EXAMPLES=100 backend sh -lc "sh ./fuzz/run_fuzzing.sh"
```

Результат сохраняется внутри backend-контейнера в `reports/fuzzing-output.txt`. Его можно скопировать на хост:

```powershell
mkdir reports -Force
docker cp "$(docker compose ps -q backend):/app/reports/fuzzing-output.txt" reports/fuzzing-output.txt
Get-Content reports/fuzzing-output.txt
```

## Безопасность

- Приватные маршруты требуют JWT.
- Роли назначаются сервером, пользователь не может сам стать admin.
- Ownership/IDOR проверяется на уровне backend.
- Секреты и CORS вынесены в env.
- База данных доступна только во внутренней Docker-сети.
- Production запускается через Gunicorn + Uvicorn worker без `--reload`.

## Облачное развёртывание

Рекомендуемая схема: Render/Amvera/VPS + PostgreSQL managed instance. Для отчёта после деплоя нужно добавить:

1. URL frontend.
2. URL Swagger/OpenAPI.
3. Скриншот healthcheck.
4. Скриншот логов deploy.
5. Commit SHA.
