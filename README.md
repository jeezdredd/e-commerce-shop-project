# Megano — интернет-магазин

Backend интернет-магазина (Django + Django REST Framework) под готовый Vue3 SPA-фронтенд
(`diploma-frontend/`). Данные отдаются по REST API с префиксом `/api/` согласно контракту
`diploma-frontend/swagger/swagger.yaml`.

## Стек
- Python 3.13+, Django, Django REST Framework
- PostgreSQL
- Celery + Redis (очередь оплаты)
- uv (менеджер зависимостей)
- Docker / docker-compose (`docker/`)

## Быстрый старт через Docker

```bash
git clone <repo>
cd e-commerce-shop-project
cp .env.example .env
docker compose -f docker/docker-compose.yml --env-file .env up -d --build
docker compose -f docker/docker-compose.yml exec web uv run python manage.py migrate
docker compose -f docker/docker-compose.yml exec web uv run python manage.py loaddata fixtures/demo.json
```

### Переменные `.env`

Для запуска через Docker-compose менять ничего не нужно — значения по умолчанию
уже согласованы с `docker-compose.yml`. Их стоит менять только в конкретных случаях:

| Переменная | Значение по умолчанию | Когда менять                                                                                                                       |
|---|---|------------------------------------------------------------------------------------------------------------------------------------|
| `SECRET_KEY` | `change-me-in-production` | На случайную строку перед деплоем в прод (Django `SECRET_KEY`)                                                                     |
| `DEBUG` | `True` | На `False` в проде - иначе Django отдаёт трейсбеки наружу                                                                          |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost,0.0.0.0` | Добавить домен/IP сервера при деплое (список через запятую)                                                                        |
| `DB_ENGINE` | `django.db.backends.postgresql` | Не менять - код рассчитан на PostgreSQL                                                                                            |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | `megano` / `megano` / `megano` | Если поднимаете свою БД (не из `docker-compose.yml`) — подставить её реквизиты                                                     |
| `DB_HOST`, `DB_PORT` | `127.0.0.1` / `5432` | При Docker-запуске оставить как есть (сеть compose сама резолвит `db`); при локальном запуске без Docker — адрес своего PostgreSQL |
| `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | `redis://127.0.0.1:6379/...` | Адрес своего Redis, если не через `docker-compose.yml`                                                                             |
| `DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD` | `admin` / `admin@megano.local` / `admin` | Логин/пароль администратора, создаваемого миграцией — сменить перед реальным деплоем                                               |

Сайт: http://127.0.0.1:8000 · Админка: http://127.0.0.1:8000/admin (admin / admin).

## Локальный запуск без Docker

Нужны запущенные PostgreSQL и Redis. Параметры подключения — в `.env`
(`DB_*`, `CELERY_BROKER_URL`).

```bash
cp .env.example .env
uv sync
uv pip install ./diploma-frontend
uv run python manage.py migrate
uv run python manage.py loaddata fixtures/demo.json      # демо-данные
uv run celery -A megano worker -l info                   # в отдельном терминале
uv run python manage.py runserver 0.0.0.0:8000
```

## Развёртывание (по шагам ТЗ)
1. `git clone`
2. правка `.env`
3. `python manage.py migrate` - создаёт схему БД, роли (`Administrator`, `Customer`),
   администратора (из `DJANGO_SUPERUSER_*`) и настройки доставки
4. запуск Redis + Celery worker
5. `python manage.py runserver 0.0.0.0:8000`

## Данные

- **Миграции** (`migrate`) ставят схему + обязательные данные: суперпользователь-админ,
  группы-роли, `DeliverySettings` (экспресс 500 ₽, порог бесплатной доставки 2000 ₽,
  базовая доставка 200 ₽ — редактируются в админке). Миграции обратимы
  (`migrate <app> zero`).
- **Демо-данные**: `loaddata fixtures/demo.json` либо `python manage.py seed_demo`.
  Покупатели с паролем `123456` (`ivan`, `petr`, `anna`), категории (2 уровня), товары,
  теги, характеристики, отзывы, скидки, заказы, баннеры.

## Тесты

```bash
uv run python manage.py test
```

## Структура
- `megano/` — настройки, celery, корневые urls
- `api/` — DRF: сериализаторы, вьюхи, роутинг `/api/`
- `accounts/` — кастомный `User`, роли, профиль
- `catalog/` — категории, товары, теги, характеристики, отзывы, скидки, `seed_demo`
- `cart/` — корзина (БД для авторизованных, сессия для гостей)
- `orders/` — заказы, `DeliverySettings`, расчёт доставки
- `payments/` — оплата, Celery-задача `process_payment`
- `common/` — мягкое удаление (`SoftDeleteModel`, `SoftDeleteAdmin`)
- `docker/` — `Dockerfile`, `docker-compose.yml`
- `diploma-frontend/` — неизменяемый фронтенд (Vue SPA)

## Логика оплаты
Номер карты/счёта: только цифры, не длиннее 8, чётный. Задача оплаты ставится в очередь
Celery. Фиктивный сервис: чётный и не оканчивается на 0 → оплата подтверждена; иначе —
случайная ошибка (текст виден в личном кабинете и истории заказов).
