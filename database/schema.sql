-- Raseef database schema (SQLite)

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    company_name TEXT,
    capital TEXT,
    equipment TEXT,
    experience TEXT,
    executed_projects TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    sector TEXT,
    source TEXT,
    source_type TEXT,
    source_url TEXT,
    value REAL,
    deadline TEXT,
    governorate TEXT,
    description TEXT,
    raw_text TEXT,
    competition TEXT,
    duration_days INTEGER,
    win_score INTEGER,
    risk_score INTEGER,
    profit_score INTEGER,
    recommendation TEXT,
    lat REAL,
    lng REAL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(title, source)
);

CREATE VIRTUAL TABLE IF NOT EXISTS projects_fts USING fts5(
    title, description, raw_text, content='projects', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS projects_ai AFTER INSERT ON projects BEGIN
    INSERT INTO projects_fts(rowid, title, description, raw_text)
    VALUES (new.id, new.title, new.description, new.raw_text);
END;

CREATE TRIGGER IF NOT EXISTS projects_ad AFTER DELETE ON projects BEGIN
    INSERT INTO projects_fts(projects_fts, rowid, title, description, raw_text)
    VALUES('delete', old.id, old.title, old.description, old.raw_text);
END;

CREATE TRIGGER IF NOT EXISTS projects_au AFTER UPDATE ON projects BEGIN
    INSERT INTO projects_fts(projects_fts, rowid, title, description, raw_text)
    VALUES('delete', old.id, old.title, old.description, old.raw_text);
    INSERT INTO projects_fts(rowid, title, description, raw_text)
    VALUES (new.id, new.title, new.description, new.raw_text);
END;

CREATE TABLE IF NOT EXISTS scrape_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    status TEXT,
    new_projects INTEGER DEFAULT 0,
    message TEXT,
    run_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    kind TEXT,
    message TEXT,
    sent_telegram INTEGER DEFAULT 0,
    sent_email INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(project_id) REFERENCES projects(id)
);
