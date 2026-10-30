import sqlite3
from datetime import datetime

DB_NAME = "berita.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            author TEXT,
            content TEXT,
            image_url TEXT,
            image_path TEXT,
            source TEXT,
            link TEXT,
            is_auto INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            views INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_manual(title, category, author, content, image_path):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now().strftime("%A, %d %B %Y - %H:%M WIB")
    cursor.execute(
        "INSERT INTO articles (title, category, author, content, image_path, is_auto, created_at) VALUES (?, ?, ?, ?, ?, 0, ?)",
        (title, category, author, content, image_path, now)
    )
    conn.commit()
    conn.close()

def add_auto(title, category, source, link, image_url, content):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM articles WHERE link = ?", (link,))
    if cursor.fetchone():
        conn.close()
        return False
    now = datetime.now().strftime("%A, %d %B %Y - %H:%M WIB")
    cursor.execute(
        "INSERT INTO articles (title, category, source, link, image_url, content, is_auto, created_at) VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
        (title, category, source, link, image_url, content, now)
    )
    conn.commit()
    conn.close()
    return True

def get_all(limit=None):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    q = "SELECT * FROM articles ORDER BY id DESC"
    if limit: q += f" LIMIT {limit}"
    cursor.execute(q)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_by_cat(cat):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles WHERE category = ? ORDER BY id DESC", (cat,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_by_id(aid):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles WHERE id = ?", (aid,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE articles SET views = views + 1 WHERE id = ?", (aid,))
        conn.commit()
    conn.close()
    return dict(row) if row else None

def get_popular(limit=5):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles ORDER BY views DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def delete(aid):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DELETE FROM articles WHERE id = ?", (aid,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database Ultimate siap!")
