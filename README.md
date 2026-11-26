# Todo List

A small Django site for managing tasks. You can create tasks, give them tags and deadlines, and mark them as done.

## Features

- **Tasks**: each task has content, a creation time, an optional deadline, a done/not done status and any number of tags.
- **Home page (`/`)**: lists all tasks. Tasks that are not done come first, and within each group the newest come first. Each task has Update and Delete links and a Complete/Undo button that switches its status.
- **Tags (`/tags/`)**: a table of tags with Update and Delete buttons. A tag can belong to many tasks. Deleting a tag doesn't delete its tasks.
- Pages for creating, editing and deleting tasks and tags. Deletion asks for confirmation first.
- A sidebar with links to Home and Tags on every page.

## Tech stack

Python 3.12, Django 6.1, SQLite, Bootstrap 5 (loaded from a CDN).

## Getting started

```bash
git clone https://github.com/olhayakubovska/todo-list.git
cd todo-list

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then set your own SECRET_KEY
python manage.py migrate
python manage.py runserver
```

Then open http://127.0.0.1:8000/.

### Environment variables

| Variable     | Description                                   |
|--------------|-----------------------------------------------|
| `SECRET_KEY` | Django secret key. Required.                  |
| `DEBUG`      | `True` for local development. Default `False`. |

To generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Running tests

```bash
python manage.py test
```

## Project structure

```
todo/               # app: models, views, forms, urls, tests
templates/          # base layout, sidebar and page templates
todo_project/       # project settings and root urls
```
