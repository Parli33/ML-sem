# ML-сервис оценки риска сердечно-сосудистых заболеваний

Веб-приложение позволяет зарегистрироваться, заполнить медицинскую анкету,
получить оценку рисков сердечно-сосудистых заболеваний и просмотреть историю
предыдущих запросов.

> Результаты модели не являются медицинским диагнозом и не заменяют
> консультацию врача.

## Возможности

- регистрация, вход и выход с использованием Flask-сессий;
- защищённые страницы, доступные только авторизованным пользователям;
- Flask-WTF формы с серверной валидацией и CSRF-защитой;
- вызов ML API из Flask по HTTP;
- оценка общего риска и рисков отдельных заболеваний;
- сохранение входных данных и результатов в PostgreSQL;
- история предсказаний текущего пользователя;
- Alembic-миграции базы данных;
- логирование операций Flask и FastAPI;
- запуск всех компонентов через Docker Compose.

## Архитектура

```text
Браузер
  |
  v
Flask Web App :5000
  | HTTP: http://fastapi:8000/predict
  +-----------------------------> FastAPI ML API :8000
  |
  +-----------------------------> PostgreSQL :5432
```

Сервисы:

- `flask` — пользовательский интерфейс, аутентификация, валидация форм,
  вызов ML API и работа с историей;
- `fastapi` — загрузка CatBoost-моделей и выполнение предсказаний;
- `db` — хранение пользователей и истории запросов в PostgreSQL.

Основные каталоги:

```text
services/
├── api_gateway/
│   ├── app/
│   │   ├── infrastructure/  # SQLAlchemy-модели и клиент ML API
│   │   ├── services/        # сервисы аутентификации и предсказаний
│   │   ├── web/             # Flask-маршруты и формы
│   │   └── templates/       # Jinja-шаблоны
│   ├── migrations/          # Alembic-миграции
│   └── tests/
└── ml_service/
    └── app/
        ├── routers/         # FastAPI-маршруты
        ├── schemas/         # Pydantic-схемы
        ├── services/        # инференс, подготовка данных и обучение
        └── models/          # файлы обученных моделей
```

## Быстрый запуск

Требования:

- Docker с Docker Compose;
- свободные порты `5000`, `8000` и `5432`.

Создайте локальный файл с переменными окружения:

```bash
cp .env.example .env
```

Замените `POSTGRES_PASSWORD` и `SECRET_KEY`, затем запустите:

```bash
docker compose -p ml-sem up --build -d
```

При первом старте Flask-контейнер автоматически применяет Alembic-миграции.

Адреса после запуска:

- Flask UI: http://localhost:5000
- FastAPI Swagger: http://localhost:8000/docs
- FastAPI healthcheck: http://localhost:8000/health
- FastAPI model info: http://localhost:8000/model-info
- PostgreSQL: `localhost:5432`

Проверка состояния:

```bash
docker compose -p ml-sem ps
docker compose -p ml-sem logs -f
```

Остановка:

```bash
docker compose -p ml-sem down
```

Удаление контейнеров вместе с данными PostgreSQL:

```bash
docker compose -p ml-sem down -v
```

`POSTGRES_PASSWORD` и `SECRET_KEY` обязательны. Без файла `.env` с заданными
секретами Docker Compose остановится с ошибкой до запуска контейнеров.

## Переменные окружения

| Переменная | Назначение | Пример |
|---|---|---|
| `POSTGRES_DB` | имя базы данных | `ml_sem` |
| `POSTGRES_USER` | пользователь PostgreSQL | `ml_user` |
| `POSTGRES_PASSWORD` | пароль PostgreSQL | случайный надёжный пароль |
| `SECRET_KEY` | подпись Flask-сессий и CSRF-токенов | случайная длинная строка |

Внутри Docker Flask использует:

```text
DATABASE_URL=postgresql+psycopg://<user>:<password>@db:5432/<database>
ML_API_URL=http://fastapi:8000
```

## Основные страницы

- `/register` — регистрация пользователя;
- `/login` — вход;
- `/` — защищённая главная страница;
- `/predict` — защищённая форма предсказания;
- `/history` — защищённая история запросов текущего пользователя.

Пароли хранятся только в виде хэша Werkzeug. История одного пользователя
недоступна другим пользователям.

## ML API

Основные конечные точки:

- `POST /predict` — принимает JSON с признаками пациента и возвращает риски;
- `GET /health` — проверка работоспособности;
- `GET /model-info` — версия, список моделей и типы признаков;

FastAPI оценивает:

- общий риск;
- артериальную гипертензию;
- стенокардию;
- нарушение ритма или ИБС;
- сердечную недостаточность;
- инфаркт миокарда;
- инсульт.

## База данных и миграции

Таблицы:

- `users` — логин, хэш пароля и дата регистрации;
- `predictions` — пользователь, входные данные, результат и дата запроса.

Для локального управления миграциями сначала экспортируйте переменные из `.env`:

```bash
set -a
source .env
set +a
export DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}"
```

Создание новой миграции:

```bash
PYTHONPATH=services/api_gateway \
uv run --package web flask --app app:create_app db migrate \
  --directory services/api_gateway/migrations -m "описание миграции"
```

Применение миграций:

```bash
PYTHONPATH=services/api_gateway \
uv run --package web flask --app app:create_app db upgrade \
  --directory services/api_gateway/migrations
```

## Локальная разработка

Проект использует Python 3.12+ и `uv` workspace.

Установка зависимостей:

```bash
uv sync --all-packages
```

Запуск Flask-тестов:

```bash
PYTHONPATH=services/api_gateway uv run --package web pytest -q services/api_gateway/tests
```

Запуск всех pre-commit проверок:

```bash
uv run pre-commit run --all-files
```

Установка автоматических Git hooks:

```bash
uv run pre-commit install --install-hooks
```

Перед коммитом автоматически запускаются Ruff и mypy для обоих сервисов.
Сообщение коммита проверяется Commitizen и должно соответствовать Conventional
Commits, например:

```text
feat: добавлена история предсказаний
fix: исправлена обработка ответа ML API
```
