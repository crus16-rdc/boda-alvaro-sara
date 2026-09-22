from flask import Flask, request, jsonify
import sqlite3
import csv
import io
from datetime import datetime

app = Flask(__name__)

DB = "/data/invitados.db"


def init_db():
    conn = sqlite3.connect(DB)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS confirmations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            names TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


@app.route("/api/rsvp", methods=["POST"])
def rsvp():

    data = request.get_json()

    if not data or "names" not in data:
        return jsonify({
            "success": False,
            "message": "No se han recibido los nombres"
        }), 400

    names = data["names"]

    if not isinstance(names, list) or len(names) == 0:
        return jsonify({
            "success": False,
            "message": "Debe haber al menos un asistente"
        }), 400

    names = [
        name.strip()
        for name in names
        if isinstance(name, str) and name.strip()
    ]

    if not names:
        return jsonify({
            "success": False,
            "message": "No hay nombres válidos"
        }), 400

    conn = sqlite3.connect(DB)

    conn.execute(
        """
        INSERT INTO confirmations (names, created_at)
        VALUES (?, ?)
        """,
        (", ".join(names), datetime.now().isoformat())
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Confirmación recibida"
    })


@app.route("/api/admin/confirmations")
def admin_confirmations():

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT id, names, created_at
        FROM confirmations
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    confirmations = [
        {
            "id": row["id"],
            "names": row["names"],
            "created_at": row["created_at"]
        }
        for row in rows
    ]

    return jsonify(confirmations)


@app.route("/api/admin/export")
def admin_export():

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT id, names, created_at
        FROM confirmations
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "Invitados",
        "Fecha"
    ])

    for row in rows:

        writer.writerow([
            row["id"],
            row["names"],
            row["created_at"]
        ])

    response = app.response_class(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8"
    )

    response.headers["Content-Disposition"] = (
        "attachment; filename=confirmaciones.csv"
    )

    return response


@app.route("/api/health")
def health():

    return jsonify({
        "status": "ok"
    })


init_db()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )
