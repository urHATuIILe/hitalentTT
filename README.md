# Org Structure API

REST API для управления организационной структурой компании: подразделения и сотрудники.

## Стек

- **FastAPI** + Python 3.12
- **PostgreSQL** + asyncpg (асинхронный драйвер)
- **SQLAlchemy** (async ORM)
- **Alembic** (миграции)
- **Pydantic v2** (валидация данных)
- **Loguru** (логирование)
- **Pytest** (тесты, включая интеграционные через SQLite in-memory)
- **Docker** + docker-compose

## Быстрый старт (Docker)

```bash
docker-compose up --build
```

После запуска:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Миграции применяются автоматически при старте контейнера.

> PostgreSQL в контейнере проброшен на хостовый порт **5433** (`5433:5432`), чтобы не конфликтовать с локально установленным PostgreSQL на 5432. Само приложение внутри Docker-сети подключается к БД по адресу `db:5432`. Если хочешь подключиться к контейнерной БД с хоста — используй порт `5433`.

## Локальный запуск (без Docker)

**1. Установить зависимости:**
```bash
pip install -r requirements.txt
```

**2. Настроить переменные окружения** — отредактировать `.env` в корне проекта:
```env
DATABASE_URL=postgresql+asyncpg://orguser:orgpass123@localhost:5432/orgstructure
SYNC_DATABASE_URL=postgresql://orguser:orgpass123@localhost:5432/orgstructure
DEBUG=true
```

**3. Применить миграции:**
```bash
alembic upgrade head
```

**4. Запустить приложение:**
```bash
uvicorn app.main:app --reload
```

## Запуск тестов

Тесты не требуют PostgreSQL — используется SQLite in-memory.

```bash
pytest tests/ -v
```

## API

| Метод    | Путь                             | Описание                            |
|----------|----------------------------------|-------------------------------------|
| `POST`   | `/departments/`                  | Создать подразделение               |
| `GET`    | `/departments/{id}`              | Получить подразделение (дерево + сотрудники) |
| `PATCH`  | `/departments/{id}`              | Переименовать / переместить         |
| `DELETE` | `/departments/{id}`              | Удалить (cascade или reassign)      |
| `POST`   | `/departments/{id}/employees/`   | Добавить сотрудника                 |
| `GET`    | `/health`                        | Health check                        |

Полная документация с примерами запросов — Swagger UI: `/docs`

### Параметры GET /departments/{id}

| Параметр            | Тип    | По умолчанию | Описание                                  |
|---------------------|--------|--------------|-------------------------------------------|
| `depth`             | int    | `1`          | Глубина вложенных подразделений (0–5)     |
| `include_employees` | bool   | `true`       | Включать ли сотрудников в ответ           |
| `sort_employees_by` | string | `created_at` | Сортировка сотрудников: `created_at` / `full_name` |

### Параметры DELETE /departments/{id}

| Параметр                    | Тип    | Описание                                               |
|-----------------------------|--------|--------------------------------------------------------|
| `mode`                      | string | `cascade` — удалить всё; `reassign` — перевести сотрудников |
| `reassign_to_department_id` | int    | Обязателен при `mode=reassign`                         |

## Структура проекта

```
app/
├── api/              # HTTP-эндпоинты (роутеры)
├── models/           # SQLAlchemy-модели (Department, Employee)
├── repositories/     # Слой доступа к данным
├── schemas/          # Pydantic-схемы (input/output)
├── services/         # Бизнес-логика
├── utils/            # Кастомные исключения, утилиты
├── config.py         # Настройки приложения (pydantic-settings)
├── database.py       # Подключение к БД
└── main.py           # Точка входа FastAPI
migrations/
├── versions/         # Файлы миграций Alembic
└── env.py
tests/
├── conftest.py       # Фикстуры (SQLite in-memory)
├── test1.py          # Тесты схем
└── test_api.py       # Интеграционные тесты API
```

## Бизнес-логика

- Имена подразделений **уникальны в рамках одного родителя**
- Пробелы по краям имён **триммируются автоматически**
- Нельзя сделать подразделение **родителем самого себя** (409)
- Нельзя создать **цикл** в дереве (409)
- При `mode=cascade` удаляются подразделение, все дочерние и все сотрудники
- При `mode=reassign` сотрудники переводятся в указанное подразделение перед удалением
