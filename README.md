# Auth Service

FastAPI-сервис, отвечающий за вход через GitHub OAuth, хранение пользователей и выдачу JWT.

## Назначение

- Перенаправляет пользователя на страницу GitHub OAuth.
- Обрабатывает callback от GitHub.
- Создает или обновляет локальную запись пользователя.
- Выдает JWT access token для фронтенда и межсервисных запросов.
- Возвращает данные текущего пользователя.

## HTTP API

- `GET /healthz` - проверка состояния сервиса.
- `GET /api/v1/auth/login/github` - начало GitHub OAuth flow.
- `GET /api/v1/auth/callback/github` - callback URL для GitHub OAuth.
- `GET /api/v1/auth/me` - данные текущего пользователя по bearer token.

## Конфигурация

Настройки читаются из переменных окружения с префиксом `AUTH_`. Для вложенных полей используется разделитель `__`.

Основные переменные:

- `AUTH_DB__HOST`
- `AUTH_DB__PORT`
- `AUTH_DB__USER`
- `AUTH_DB__NAME`
- `AUTH_DB__PASSWORD`
- `AUTH_AUTH__JWT_SECRET`
- `AUTH_GITHUB__CLIENT_ID`
- `AUTH_GITHUB__CLIENT_SECRET`
- `AUTH_GITHUB__WEBHOOK_SECRET`
- `AUTH_SERVER__PORT`
- `AUTH_SERVER__BASE_URL`
- `AUTH_SERVER__FRONTEND_URL`
- `AUTH_DEPLOYMENTS_SERVICE__BASE_URL`
- `DB_ADMIN_URL` - используется Alembic-миграциями.

## Локальный запуск

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

Запуск тестов:

```bash
pytest -q
```

## Миграции

Сервис использует Alembic. `DB_ADMIN_URL` должен указывать на целевую БД и иметь достаточные права.

```bash
alembic upgrade head
```

## Деплой

Helm chart находится в `charts/auth-service`. GitHub Actions workflow собирает Docker image и деплоит сервис через Helm.

Значения для деплоя задаются через repository variables и secrets: registry endpoint, имя Kubernetes-кластера, GitHub OAuth credentials, пароли БД и `JWT_SECRET`.
