# UML: диаграмма компонентов

Схема показывает части проекта в его текущей структуре. Регистрация и вход добавлены на сервере как начальная работа; формы страницы ещё предстоит с ними связать.

```mermaid
flowchart LR
    User[Пользователь] --> Browser[Браузер]
    subgraph App[Проект]
        Page[index.html<br/>HTML CSS JavaScript]
        Server[server.py<br/>Python http.server]
        Schema[schema.sql<br/>структура таблиц]
        DB[(SQLite<br/>data/forma.sqlite3)]
        Auth[Начальные адреса<br/>регистрация и вход]
        Browser -->|HTTP| Server
        Server -->|отдаёт страницу| Page
        Server --> Auth
        Server -->|читает и сохраняет| DB
        Schema -->|создаёт таблицы| DB
        Auth -->|пользователи и сессии| DB
    end
```

- `index.html` — страница, которую видит пользователь.
- `server.py` — принимает запросы и обрабатывает их на Python.
- `schema.sql` — описывает таблицы.
- SQLite — локальный файл базы данных.
- Следующий шаг — связать экранные формы с серверными адресами.
