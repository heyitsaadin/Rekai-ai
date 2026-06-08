import os
import json as _json_mod
from datetime import datetime
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash

DATABASE_URL = os.environ.get("DATABASE_URL")
db_pool = None

def init_db_pool():
    global db_pool
    if db_pool is None and DATABASE_URL:
        db_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=DATABASE_URL
        )

def get_db():
    if db_pool is None:
        init_db_pool()
    if db_pool is None:
        return None
    return db_pool.getconn()

def return_db(conn):
    if db_pool and conn:
        db_pool.putconn(conn)

def init_db():
    conn = get_db()
    if conn is None:
        return
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users    (username TEXT PRIMARY KEY, password TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS history  (username TEXT, calculation TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS visits   (timestamp TEXT, date TEXT)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            username     TEXT PRIMARY KEY,
            profile_json TEXT,
            last_updated TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id          SERIAL PRIMARY KEY,
            username    TEXT,
            session_key TEXT,
            messages    TEXT,
            created_at  TEXT,
            updated_at  TEXT,
            is_pinned   BOOLEAN DEFAULT FALSE,
            UNIQUE(username, session_key)
        )
    """)
    conn.commit()
    try:
        cur.execute("ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE")
        conn.commit()
    except Exception:
        conn.rollback()
    try:
        cur.execute("""
            DELETE FROM chat_sessions
            WHERE id NOT IN (
                SELECT MAX(id) FROM chat_sessions GROUP BY username, session_key
            )
        """)
        conn.commit()
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uniq_user_session ON chat_sessions(username, session_key)")
        conn.commit()
    except Exception:
        conn.rollback()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            id         SERIAL PRIMARY KEY,
            type       TEXT,
            value      TEXT UNIQUE,
            reason     TEXT,
            banned_at  TEXT,
            banned_by  TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS shared_chats (
            share_token TEXT PRIMARY KEY,
            username    TEXT,
            session_key TEXT,
            messages    TEXT,
            title       TEXT,
            shared_at   TEXT
        )
    """)
    conn.commit()
    cur.close()
    return_db(conn)

def get_user(username):
    conn = get_db()
    if conn is None:
        return None
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    cur.close()
    return_db(conn)
    return user

def add_user(username, password):
    conn = get_db()
    if conn is None:
        return
    cur = conn.cursor()
    cur.execute("INSERT INTO users VALUES (%s, %s)", (username, generate_password_hash(password)))
    conn.commit()
    cur.close()
    return_db(conn)

def update_username_db(old_username, new_username):
    conn = get_db()
    if conn is None:
        return
    cur = conn.cursor()
    cur.execute("UPDATE users            SET username=%s WHERE username=%s", (new_username, old_username))
    cur.execute("UPDATE history          SET username=%s WHERE username=%s", (new_username, old_username))
    cur.execute("UPDATE user_profiles    SET username=%s WHERE username=%s", (new_username, old_username))
    cur.execute("UPDATE chat_sessions    SET username=%s WHERE username=%s", (new_username, old_username))
    conn.commit()
    cur.close()
    return_db(conn)

def update_password_db(username, new_password):
    conn = get_db()
    if conn is None:
        return
    cur = conn.cursor()
    cur.execute("UPDATE users SET password=%s WHERE username=%s",
                (generate_password_hash(new_password), username))
    conn.commit()
    cur.close()
    return_db(conn)

def save_history(username, calculation):
    conn = get_db()
    if conn is None:
        return
    cur = conn.cursor()
    cur.execute("INSERT INTO history VALUES (%s, %s)", (username, calculation))
    conn.commit()
    cur.close()
    return_db(conn)

def get_profile(username, TOPIC_KEYWORDS=None):
    conn = get_db()
    if conn is None:
        return {
            "interests": {k: 0 for k in (TOPIC_KEYWORDS or {})},
            "total_messages": 0,
            "user_messages": 0,
            "avg_length": 0,
            "peak_hour": None,
            "hour_counts": {},
            "top_topics": [],
            "sentiment": "neutral",
            "last_groq_analysis": None,
            "groq_summary": ""
        }
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT profile_json FROM user_profiles WHERE username=%s", (username,))
    row = cur.fetchone()
    cur.close()
    return_db(conn)
    if row:
        return _json_mod.loads(row["profile_json"])
    return {
        "interests": {k: 0 for k in (TOPIC_KEYWORDS or {})},
        "total_messages": 0,
        "user_messages": 0,
        "avg_length": 0,
        "peak_hour": None,
        "hour_counts": {},
        "top_topics": [],
        "sentiment": "neutral",
        "last_groq_analysis": None,
        "groq_summary": ""
    }

def save_profile(username, profile, IST=None):
    conn = get_db()
    if conn is None:
        return
    cur = conn.cursor()
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M") if IST else datetime.now().strftime("%Y-%m-%d %H:%M")
    cur.execute("""
        INSERT INTO user_profiles (username, profile_json, last_updated)
        VALUES (%s, %s, %s)
        ON CONFLICT (username) DO UPDATE SET profile_json=%s, last_updated=%s
    """, (username, _json_mod.dumps(profile), now, _json_mod.dumps(profile), now))
    conn.commit()
    cur.close()
    return_db(conn)

def get_chat_sessions(username):
    conn = get_db()
    if conn is None:
        return []
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT id, session_key, messages, created_at, updated_at, COALESCE(is_pinned, FALSE) as is_pinned "
        "FROM chat_sessions WHERE username=%s ORDER BY is_pinned DESC, updated_at DESC",
        (username,)
    )
    rows = cur.fetchall()
    cur.close()
    return_db(conn)
    return rows

def get_chat_session(username, session_key):
    conn = get_db()
    if conn is None:
        return None
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT id, session_key, messages, created_at, updated_at, COALESCE(is_pinned, FALSE) as is_pinned "
        "FROM chat_sessions WHERE username=%s AND session_key=%s",
        (username, session_key)
    )
    row = cur.fetchone()
    cur.close()
    return_db(conn)
    return row

def save_chat_session(username, session_key, messages, IST=None):
    conn = get_db()
    if conn is None:
        return
    cur = conn.cursor()
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M") if IST else datetime.now().strftime("%Y-%m-%d %H:%M")
    cur.execute("""
        INSERT INTO chat_sessions (username, session_key, messages, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (username, session_key) DO UPDATE
            SET messages=%s, updated_at=%s
    """, (username, session_key, _json_mod.dumps(messages), now, now,
          _json_mod.dumps(messages), now))
    conn.commit()
    cur.close()
    return_db(conn)

def delete_chat_session(username, session_key):
    conn = get_db()
    if conn is None:
        return
    cur = conn.cursor()
    cur.execute("DELETE FROM chat_sessions WHERE username=%s AND session_key=%s",
                (username, session_key))
    conn.commit()
    cur.close()
    return_db(conn)

def delete_all_chat_sessions(username):
    conn = get_db()
    if conn is None:
        return
    cur = conn.cursor()
    cur.execute("DELETE FROM chat_sessions WHERE username=%s", (username,))
    conn.commit()
    cur.close()
    return_db(conn)

def pin_chat_session(username, session_key, is_pinned):
    conn = get_db()
    if conn is None:
        return
    cur = conn.cursor()
    cur.execute("UPDATE chat_sessions SET is_pinned=%s WHERE username=%s AND session_key=%s",
                (is_pinned, username, session_key))
    conn.commit()
    cur.close()
    return_db(conn)

def is_banned(value, ban_type):
    conn = get_db()
    if conn is None:
        return False
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM bans WHERE type=%s AND value=%s", (ban_type, value))
    found = cur.fetchone() is not None
    cur.close()
    return_db(conn)
    return found

def add_ban(ban_type, value, reason, banned_by, IST=None):
    conn = get_db()
    if conn is None:
        return
    cur = conn.cursor()
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M") if IST else datetime.now().strftime("%Y-%m-%d %H:%M")
    cur.execute("""
        INSERT INTO bans (type, value, reason, banned_at, banned_by)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (value) DO UPDATE SET reason=%s, banned_at=%s, banned_by=%s
    """, (ban_type, value, reason, now, banned_by, reason, now, banned_by))
    conn.commit()
    cur.close()
    return_db(conn)

def remove_ban(value):
    conn = get_db()
    if conn is None:
        return
    cur = conn.cursor()
    cur.execute("DELETE FROM bans WHERE value=%s", (value,))
    conn.commit()
    cur.close()
    return_db(conn)

def get_all_bans():
    conn = get_db()
    if conn is None:
        return []
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM bans ORDER BY banned_at DESC")
    rows = cur.fetchall()
    cur.close()
    return_db(conn)
    return rows

def log_visit(IST=None):
    conn = get_db()
    if conn is None:
        return
    cur = conn.cursor()
    now = datetime.now(IST) if IST else datetime.now()
    cur.execute("INSERT INTO visits VALUES (%s, %s)",
                (now.strftime("%Y-%m-%d %H:%M"), now.strftime("%Y-%m-%d")))
    conn.commit()
    cur.close()
    return_db(conn)

def save_shared_chat(username, session_key, messages, title, share_token, IST=None):
    conn = get_db()
    if conn is None:
        return
    cur = conn.cursor()
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M") if IST else datetime.now().strftime("%Y-%m-%d %H:%M")
    cur.execute("""
        INSERT INTO shared_chats (share_token, username, session_key, messages, title, shared_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (share_token, username, session_key, _json_mod.dumps(messages), title, now))
    conn.commit()
    cur.close()
    return_db(conn)

def get_shared_chat(share_token):
    conn = get_db()
    if conn is None:
        return None
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM shared_chats WHERE share_token=%s", (share_token,))
    row = cur.fetchone()
    cur.close()
    return_db(conn)
    if row:
        row['messages'] = _json_mod.loads(row['messages'])
    return row
