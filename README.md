# Защищённый REST API

Мини‑блог с регистрацией, аутентификацией по JWT и CRUD для постов. Проект содержит меры защиты от SQLi/XSS, безопасное хранение паролей и проверяется SAST/SCA в CI/CD.

## Стек
- Flask 3, Python 3.11+
- PostgreSQL + psycopg (параметризованные запросы)
- JWT (PyJWT) для авторизации, bcrypt для паролей
- Bandit и Safety для статического/зависимостного анализа

## Запуск
1) Установить зависимости: `pip install -r requirements.txt`
2) Подготовить PostgreSQL и задать переменные окружения:
   - `DATABASE_URL=postgresql://user:password@host:port/dbname`
   - `FLASK_HOST=0.0.0.0`
   - `FLASK_PORT=5000`
   - `FLASK_DEBUG=true`
   - `SECRET_KEY=example`
   - `JWT_SECRET=example`
   - `JWT_ALG=HS256`
   - `JWT_EXP_MINUTES=30`
3) Запуск: `python app.py` (инициализирует таблицы, поднимает API).

## Схема данных
- `users(id, username unique, password_hash)`
- `posts(id, title, body, owner_id)`

## Эндпоинты
- `POST /auth/register` (публичный) — создать пользователя и получить JWT.

Пример вызова:
```
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "Anton", "password": "secret"}'
```

- `POST /auth/login` (публичный) — получить JWT.

Пример вызова:
```
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "Anton", "password": "secret"}'
```

- `GET /api/data` (JWT) — список постов текущего пользователя.

Пример вызова:
```
curl -X GET http://localhost:5000/api/data \
  -H "Authorization: Bearer <TOKEN>"
```

- `POST /api/data` (JWT) — создать пост.

Пример вызова:
```
curl -X POST http://localhost:5000/api/data \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title": "title", "body": "body"}'
```


## Меры защиты
- Аутентификация: JWT c `sub` и `exp`. Проверка осуществляется в декораторе `login_required`, привязка пользователя к `g.current_user`, что позволяет получать информацию о текущем пользователе из JWT токена.
- Защита паролей: `bcrypt` (salt+hash), верификация через `checkpw`, в БД хранится хеш от пароля+соль, а не в открытом виде.
- SQLi: все запросы через `psycopg` с плейсхолдерами `%s` и параметрами, никакой конкатенации строк.
- XSS: все заголовки и тела постов экранируются `html.escape` перед выдачей и при создании ответа.
- Управление секретами: чувствительные ключи читаются из переменных окружения через `python-dotenv`.

## CI/CD и отчёты SAST/SCA
- Статический анализ: `bandit -r .`.

Результат:\
![alt text](bandit.png)  

- Анализ зависимостей: `safety check -r requirements.txt`.

Результат:\
![alt text](safety.png)

