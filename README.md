# Process Manager

A simple Django web app for remote monitoring and control of processes on the machine where the app runs. Uses HTMX for client–server interactions and requires login to access.

## Features

- **Process Browser** – List of active processes (PID, name, status, start time, duration, CPU %, memory). Filters (PID, status, name), sortable columns (PID, name, CPU, memory), “Kill Process” per row, “Take Snapshot”, auto-refresh every 30s. Process with PID 0 is skipped.
- **Snapshots** – Save the current process list with timestamp and author. Browse snapshots, view details, export to Excel. Charts show CPU usage, memory usage, and process count over time (from snapshot data).
- **Kill Log** – List of “Kill Process” actions with timestamp, author, and process name.
- **Login** – Simple login only; no registration. Users are created from the CLI.

## Requirements

- Python 3.12+
- See `requirements.txt` for dependencies (Django, psutil, openpyxl, etc.)

## Setup

1. **Clone or unpack** the project and go to the project root (where `manage.py` is).

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations:**

   ```bash
   python manage.py migrate
   ```

5. **Create a user** (no in-app registration):

   ```bash
   python manage.py createsuperuser
   ```

   Enter username, email (optional), and password.

## Run

```bash
python manage.py runserver
```

Open http://localhost:8000/ in a browser. You will be redirected to the login page; after logging in you can use the Process Manager, Snapshots, and Kill Log.

## Testing and CI

Install dev dependencies first: `pip install -r requirements-dev.txt`

- **Run tests:** `python manage.py test monitor`
- **Lint:** `ruff check .`
- **Type check:** `mypy monitor process_manager`

GitHub Actions runs on push/PR to `main` or `master`: installs dependencies, runs migrations, tests, Ruff, and Mypy (see `.github/workflows/ci.yml`). Matrix: Python 3.10 and 3.12.

## Project structure

- `process_manager/` – Django project settings and root URL config.
- `monitor/` – Main app: models (Snapshot, KillLog), views, URLs, templates.
- `templates/` – Global templates (base, login).
- `requirements.txt` – Python dependencies.
- `requirements-dev.txt` – Dev dependencies (Ruff, Mypy, django-stubs).
- `pyproject.toml` – Ruff and Mypy config.

## Notes

- **Admin** – Staff users see an “Admin” link in the nav; Django admin is at `/admin/`.
- **Snapshots** – Stored in the database; charts on the Snapshots page use only snapshot data.
- **Kill** – Sends SIGTERM; permission errors (e.g. killing PID 1) are shown in the UI.
