"""
Raseef Backend — Flask + SQLite + JWT (كل المكونات مجانية ومفتوحة المصدر)
تشغيل:
    pip install -r backend/requirements.txt
    python database/init_db.py
    python backend/app.py
"""
import os
import sys
import sqlite3
import datetime
from functools import wraps

import jwt
from flask import Flask, request, jsonify, g, Response
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.export import projects_to_csv, project_to_proposal_txt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "raseef.db")
SECRET_KEY = os.environ.get("RASEEF_SECRET", "dev-secret-change-me")

app = Flask(__name__)
CORS(app)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "الرجاء تسجيل الدخول"}), 401
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            g.user_id = payload["user_id"]
        except jwt.PyJWTError:
            return jsonify({"error": "جلسة غير صالحة"}), 401
        return f(*args, **kwargs)
    return wrapper


@app.post("/api/register")
def register():
    data = request.json
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, password_hash, company_name) VALUES (?,?,?)",
            (data["username"], generate_password_hash(data["password"]), data.get("company_name", "")),
        )
        db.commit()
        return jsonify({"message": "تم إنشاء الحساب"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "اسم المستخدم مستخدم مسبقاً"}), 400


@app.post("/api/login")
def login():
    data = request.json
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=?", (data["username"],)).fetchone()
    if not user or not check_password_hash(user["password_hash"], data["password"]):
        return jsonify({"error": "بيانات الدخول غير صحيحة"}), 401
    token = jwt.encode(
        {"user_id": user["id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)},
        SECRET_KEY, algorithm="HS256",
    )
    return jsonify({"token": token})


@app.get("/api/projects")
def list_projects():
    db = get_db()
    sector = request.args.get("sector")
    governorate = request.args.get("governorate")
    search = request.args.get("search")
    high_only = request.args.get("high_only") == "true"
    sort_by = request.args.get("sort_by", "win_score")

    if search:
        rows = db.execute(
            """SELECT p.* FROM projects p
               JOIN projects_fts f ON p.id = f.rowid
               WHERE projects_fts MATCH ?
               ORDER BY p.win_score DESC""",
            (search,),
        ).fetchall()
    else:
        query = "SELECT * FROM projects WHERE 1=1"
        params = []
        if sector:
            query += " AND sector=?"
            params.append(sector)
        if governorate:
            query += " AND governorate=?"
            params.append(governorate)
        if high_only:
            query += " AND win_score >= 65"
        query += f" ORDER BY {sort_by} DESC"
        rows = db.execute(query, params).fetchall()

    return jsonify([dict(r) for r in rows])


@app.get("/api/projects/<int:pid>")
def get_project(pid):
    db = get_db()
    row = db.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    if not row:
        return jsonify({"error": "غير موجود"}), 404
    return jsonify(dict(row))


@app.post("/api/scrape/run")
@require_auth
def trigger_scrape():
    from scraper.run_scraper import run as run_scraper
    run_scraper()
    return jsonify({"message": "تم تشغيل السحب"})


@app.get("/api/scrape/status")
def scrape_status():
    db = get_db()
    logs = db.execute("SELECT * FROM scrape_log ORDER BY run_at DESC LIMIT 5").fetchall()
    today_count = db.execute(
        "SELECT COUNT(*) as c FROM projects WHERE date(created_at) = date('now')"
    ).fetchone()["c"]
    return jsonify({
        "logs": [dict(r) for r in logs],
        "new_today": today_count,
    })


@app.get("/api/company")
@require_auth
def get_company():
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id=?", (g.user_id,)).fetchone()
    return jsonify(dict(row))


@app.post("/api/company")
@require_auth
def update_company():
    data = request.json
    db = get_db()
    db.execute(
        """UPDATE users SET company_name=?, capital=?, equipment=?, experience=?, executed_projects=?
           WHERE id=?""",
        (data.get("company_name"), data.get("capital"), data.get("equipment"),
         data.get("experience"), data.get("executed_projects"), g.user_id),
    )
    db.commit()
    return jsonify({"message": "تم الحفظ"})


@app.get("/api/export/csv")
def export_csv():
    db = get_db()
    rows = [dict(r) for r in db.execute("SELECT * FROM projects ORDER BY win_score DESC").fetchall()]
    csv_text = projects_to_csv(rows)
    return Response(csv_text, mimetype="text/csv",
                     headers={"Content-Disposition": "attachment; filename=raseef_projects.csv"})


@app.get("/api/export/txt/<int:pid>")
@require_auth
def export_txt(pid):
    db = get_db()
    project = db.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    company = db.execute("SELECT * FROM users WHERE id=?", (g.user_id,)).fetchone()
    if not project:
        return jsonify({"error": "غير موجود"}), 404
    text = project_to_proposal_txt(dict(project), dict(company))
    return Response(text, mimetype="text/plain",
                     headers={"Content-Disposition": "attachment; filename=proposal.txt"})


@app.get("/api/notifications")
def get_notifications():
    db = get_db()
    rows = db.execute("SELECT * FROM notifications ORDER BY created_at DESC LIMIT 30").fetchall()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    app.run(debug=True, port=5000)
