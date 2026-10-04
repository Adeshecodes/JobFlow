# JobFlow

JobFlow is an original full-stack application tracker. It demonstrates a real REST API, CRUD operations, SQLite persistence, validation, filtering, and a responsive frontend.

## Stack

- Python and Flask
- SQLite
- HTML, CSS, and JavaScript

## Run locally

```powershell
cd jobflow
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py app.py
```

Open `http://127.0.0.1:5000` in a browser. The first run creates `jobflow.db` and adds three example records. That local database is ignored from source control by the included `.gitignore`.

## Interview walkthrough

Explain the flow clearly: the browser calls the Flask REST endpoints; Flask validates input and reads/writes data in SQLite; JavaScript redraws the table and statistics without reloading the page.
