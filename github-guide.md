# Как создать репозиторий проекта на GitHub

## Что нужно сделать тебе

1. Войди в свой аккаунт на GitHub. Если аккаунта ещё нет, создай его.
2. Нажми **New repository** и назови репозиторий, например `individual-fitness-trainer`.
3. Если преподавателю нужна ссылка для проверки, выбери **Public** либо оставь **Private** и добавь преподавателя в collaborators. Уточни у преподавателя, какой вариант требуется.
4. Не ставь флажки добавления README, `.gitignore` или лицензии: эти файлы уже подготовлены в проекте.
5. После создания GitHub покажет ссылку репозитория вида `https://github.com/ТВОЙ-ЛОГИН/individual-fitness-trainer.git`.
6. Открой проект из папки на компьютере в GitHub Desktop, сделай первый коммит всех подготовленных файлов и нажми **Publish repository** / **Push origin**. Если GitHub Desktop сообщает, что папка не является репозиторием, выбери **Add an Existing Repository** и укажи папку проекта.
7. Проверь на cтранице GitHub, что видны README, `docs/` и `outputs/index.html`. Скопируй ссылку на репозиторий для сдачи преподавателю.

## Папка проекта и состав репозитория

Локальная папка проекта:

```text
C:\Users\Admin\Documents\Codex\2026-09-27\new-chat\
```

Именно её целиком нужно подключить к GitHub. В репозитории должны быть:

```text
new-chat/
├── README.md
├── .gitignore
├── docs/
│   ├── technical-specification.md
│   ├── component-diagram.md
│   ├── sequence-diagram.md
│   ├── weekly-plan.md
│   └── github-guide.md
└── outputs/
    └── index.html
```

Папка `work/` предназначена для временных черновиков и исключена из Git. Учебные DOCX-отчёты с персональными сведениями не нужно публиковать: требования из них уже перенесены в проектные документы. Не загружай настоящие пароли, ключи, токены или персональные данные пользователей.

## Если используешь командную строку

Открой PowerShell в папке проекта и проверь:

```powershell
git status
```

Для первого коммита:

```powershell
git add README.md .gitignore docs outputs
git commit -m "docs: add project prototype and requirements"
git branch -M main
git remote add origin https://github.com/ТВОЙ-ЛОГИН/individual-fitness-trainer.git
git push -u origin main
```

Если `origin` уже существует, сначала проверь его командой `git remote -v`; повторно добавлять тот же remote не надо. После первой публикации обычный порядок такой:

```powershell
git status
git add .
git commit -m "feat: кратко описать сделанное"
git push
```

Создавай коммиты небольшими осмысленными порциями: например, отдельно добавление регистрации, отдельно сохранение профиля, отдельно экран прогресса. В конце каждой недели обновляй `docs/weekly-plan.md` и тоже фиксируй это коммитом.
