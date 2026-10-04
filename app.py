from datetime import date, datetime
from pathlib import Path
import sqlite3

from flask import Flask, jsonify, request


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "jobflow.db"
app = Flask(__name__, static_folder="static", static_url_path="")

VALID_STATUSES = {"Saved", "Applied", "Interview", "Offer", "Rejected"}


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def serialise(row):
    return dict(row)


def initialise_database():
    with get_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Saved',
                date_applied TEXT,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        existing = connection.execute("SELECT COUNT(*) AS count FROM applications").fetchone()["count"]
        if existing == 0:
            connection.executemany(
                """
                INSERT INTO applications (company, role, location, status, date_applied, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("BrightPath", "Junior Web Developer", "Remote", "Interview", "2026-09-08", "Prepare a short walkthrough of JobFlow.", datetime.now().isoformat()),
                    ("Lumen Labs", "Frontend Developer", "Lagos, Nigeria", "Applied", "2026-09-13", "Follow up after one week.", datetime.now().isoformat()),
                    ("Northstar", "Software Engineering Intern", "Remote", "Saved", None, "Tailor CV before applying.", datetime.now().isoformat()),
                ],
            )


def validate_payload(payload):
    company = str(payload.get("company", "")).strip()
    role = str(payload.get("role", "")).strip()
    status = str(payload.get("status", "Saved")).strip()
    if not company or not role:
        return None, "Company and role are required."
    if status not in VALID_STATUSES:
        return None, "Choose a valid application status."
    return {
        "company": company,
        "role": role,
        "location": str(payload.get("location", "")).strip(),
        "status": status,
        "date_applied": payload.get("date_applied") or None,
        "notes": str(payload.get("notes", "")).strip(),
    }, None


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/applications")
def list_applications():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    query = "SELECT * FROM applications"
    parameters = []
    clauses = []
    if search:
        clauses.append("(company LIKE ? OR role LIKE ? OR location LIKE ?)")
        wildcard = f"%{search}%"
        parameters.extend([wildcard, wildcard, wildcard])
    if status and status in VALID_STATUSES:
        clauses.append("status = ?")
        parameters.append(status)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY COALESCE(date_applied, created_at) DESC, id DESC"
    with get_db() as connection:
        rows = connection.execute(query, parameters).fetchall()
    return jsonify([serialise(row) for row in rows])


@app.get("/api/stats")
def application_stats():
    with get_db() as connection:
        total = connection.execute("SELECT COUNT(*) AS count FROM applications").fetchone()["count"]
        rows = connection.execute("SELECT status, COUNT(*) AS count FROM applications GROUP BY status").fetchall()
    counts = {status: 0 for status in VALID_STATUSES}
    counts.update({row["status"]: row["count"] for row in rows})
    return jsonify({"total": total, **counts})


@app.post("/api/applications")
def create_application():
    payload, error = validate_payload(request.get_json(silent=True) or {})
    if error:
        return jsonify({"error": error}), 400
    with get_db() as connection:
        cursor = connection.execute(
            """
            INSERT INTO applications (company, role, location, status, date_applied, notes, created_at)
            VALUES (:company, :role, :location, :status, :date_applied, :notes, :created_at)
            """,
            {**payload, "created_at": datetime.now().isoformat()},
        )
        row = connection.execute("SELECT * FROM applications WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(serialise(row)), 201


@app.patch("/api/applications/<int:application_id>")
def update_application(application_id):
    payload, error = validate_payload(request.get_json(silent=True) or {})
    if error:
        return jsonify({"error": error}), 400
    with get_db() as connection:
        found = connection.execute("SELECT id FROM applications WHERE id = ?", (application_id,)).fetchone()
        if not found:
            return jsonify({"error": "Application not found."}), 404
        connection.execute(
            """
            UPDATE applications
            SET company = :company, role = :role, location = :location, status = :status,
                date_applied = :date_applied, notes = :notes
            WHERE id = :id
            """,
            {**payload, "id": application_id},
        )
        row = connection.execute("SELECT * FROM applications WHERE id = ?", (application_id,)).fetchone()
    return jsonify(serialise(row))


@app.delete("/api/applications/<int:application_id>")
def delete_application(application_id):
    with get_db() as connection:
        cursor = connection.execute("DELETE FROM applications WHERE id = ?", (application_id,))
    if cursor.rowcount == 0:
        return jsonify({"error": "Application not found."}), 404
    return "", 204


if __name__ == "__main__":
    initialise_database()
    app.run(debug=True)
