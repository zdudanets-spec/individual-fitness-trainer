# Как работать с репозиторием на GitHub

Папка проекта на компьютере: `C:\Users\Admin\Documents\Codex\2026-09-27\new-chat\`.

В GitHub нужно загрузить файлы проекта из этой папки. Сам файл базы `data/forma.sqlite3` загружать не нужно: он создаётся автоматически при запуске и исключён из Git.

```text
new-chat/
├── README.md
├── .gitignore
├── backend/
│   ├── server.py
│   └── schema.sql
├── docs/
│   ├── technical-specification.md
│   ├── mvp-scope.md
│   ├── component-diagram.md
│   ├── sequence-diagram.md
│   ├── data-model.md
│   ├── weekly-plan.md
│   └── github-guide.md
└── outputs/
    └── index.html
```

## Как загрузить новые изменения

Если репозиторий уже есть на GitHub, после обновления файлов открой GitHub Desktop, посмотри список изменений, введи короткое название коммита, например `feat: add Python server and SQLite schema`, и нажми **Commit to main**, затем **Push origin**.

Если работаешь через командную строку, открой PowerShell в папке проекта и выполни:

```powershell
git status
git add .
git commit -m "feat: add Python server and SQLite schema"
git push
```

Перед загрузкой проверь, что в коммит не попали пароли, личные данные или файл базы SQLite. Для запуска проекта сторонние Python-библиотеки не нужны.
