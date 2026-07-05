"""
تهيئة قاعدة البيانات (SQLite) — يُشغَّل مرة واحدة عند بدء المشروع.
تشغيل:  python database/init_db.py
"""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "raseef.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"✅ تم إنشاء قاعدة البيانات في: {DB_PATH}")


if __name__ == "__main__":
    init_db()
