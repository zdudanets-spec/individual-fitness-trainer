# UML: диаграммы последовательностей

## 1. Запуск сайта и базы

\`\`\`mermaid
sequenceDiagram
    actor Student as Студент
    participant Python as Python
    participant Server as server.py
    participant DB as SQLite
    participant Browser as Браузер
    Student->>Python: python server.py
    Python->>Server: Запустить сервер и создать таблицы
    Server->>DB: Выполнить schema.sql
    Browser->>Server: GET /
    Server-->>Browser: Вернуть index.html
    Browser->>Server: GET /api/health/
    Server->>DB: SELECT 1
    Server-->>Browser: База доступна
\`\`\`

## 2. Регистрация и вход (начальная серверная версия)

\`\`\`mermaid
sequenceDiagram
    actor User as Пользователь
    participant Browser as Браузер
    participant Server as Python-сервер
    participant DB as SQLite
    User->>Browser: Вводит имя, почту и пароль
    Browser->>Server: POST /api/register
    Server->>Server: Проверяет поля и хеширует пароль
    Server->>DB: Сохраняет пользователя и сессию
    Server-->>Browser: Возвращает аккаунт и cookie сессии
    User->>Browser: Вводит почту и пароль
    Browser->>Server: POST /api/login
    Server->>DB: Находит аккаунт и проверяет хеш
    Server-->>Browser: Создаёт сессию
\`\`\`

Экранные формы пока не подключены к этим адресам. Подключение и ручная проверка запланированы на текущую неделю.
