# Диаграммы последовательностей

Первая диаграмма описывает подготовленный каркас. Следующие две показывают запланированные действия пользователя.

## 1. Запуск сайта и создание базы

```mermaid
sequenceDiagram
    actor Student as Студент
    participant Python as Python
    participant Server as backend/server.py
    participant SQL as backend/schema.sql
    participant DB as SQLite
    participant Browser as Браузер
    Student->>Python: py backend/server.py
    Python->>Server: Запустить сервер
    Server->>SQL: Прочитать описание таблиц
    Server->>DB: Создать базу и таблицы, если их ещё нет
    DB-->>Server: База готова
    Browser->>Server: GET /
    Server-->>Browser: Вернуть outputs/index.html
    Browser->>Server: GET /api/health/
    Server->>DB: SELECT 1
    DB-->>Server: Соединение работает
    Server-->>Browser: status ok, database connected
```

## 2. Регистрация и заполнение анкеты (будет реализовано)

```mermaid
sequenceDiagram
    actor User as Пользователь
    participant Browser as Браузер
    participant Server as Python-сервер
    participant DB as SQLite
    User->>Browser: Заполняет форму регистрации
    Browser->>Server: Отправляет имя, почту и пароль
    Server->>Server: Проверяет данные и создаёт хеш пароля
    Server->>DB: Сохраняет пользователя
    DB-->>Server: Аккаунт создан
    Server-->>Browser: Показывает анкету
    User->>Browser: Заполняет цель и параметры
    Browser->>Server: Отправляет ответы анкеты
    Server->>DB: Сохраняет профиль пользователя
    DB-->>Server: Профиль сохранён
    Server-->>Browser: Показывает подтверждение
```

## 3. План, тренировка и привычки (будет реализовано)

```mermaid
sequenceDiagram
    actor User as Пользователь
    participant Browser as Браузер
    participant Server as Python-сервер
    participant DB as SQLite
    User->>Browser: Просит составить план
    Browser->>Server: Передаёт запрос
    Server->>DB: Получает профиль и упражнения
    DB-->>Server: Возвращает нужные записи
    Server->>Server: Подбирает план по простым правилам
    Server->>DB: Сохраняет план
    Server-->>Browser: Показывает план и инструкции
    User->>Browser: Отмечает занятие, воду и шаги
    Browser->>Server: Передаёт отметки
    Server->>DB: Сохраняет результаты и привычки
    DB-->>Server: Данные сохранены
    Server-->>Browser: Показывает историю и прогресс
```
