Нужны Python 3.11+, Git и uv.

- `starter.py` — расчёт рекомендуемой цены, пример запуска и два теста.
- `answers.md` — вопросы к задаче и описание архитектуры.

Клонирование и установка зависимостей:

```bash
git clone https://github.com/Kiselaw/tolkoopt_test_task.git
cd tolkoopt_test_task
uv sync
```

Запуск скрипта:

```bash
uv run python starter.py
```

Запуск тестов:

```bash
uv run pytest -q
```
