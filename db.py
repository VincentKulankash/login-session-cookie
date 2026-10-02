#SQLite helpers: init, queries, tokens

import sqlite3
import os
from datetime import datetime, timedelta

#sqlite3 is the python inbuilt module that lets you communicate with SQLite engine
#os build the path to app.db reliably regardless of where you run the script
#datetime, timedelta compute token expiry (now + 30 days) and write timestamps 

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')


def get_connection():
    conn =sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA Foreign_keys = ON')
    return conn

def init_db():
    conn = get_connection()
    try:
        with open(os.path.join(os.path.dirname(__file__), 'schema.sql')) as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()



"""User queries"""
def create_user(username, password_hash):
    conn = get_connection()
    try: 
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?,?)",
            (username, password_hash),
        )
        conn.commit()
        return cursor.lastrowid
    finally: 
        conn.close()

def get_user_by_username(username):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None
    finally: 
        conn.close()

def get_user_by_id(user_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE id=?", (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def touch_login(user_id):
    """Update last login at and increment login count this is called after a successful login"""
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE users 
            SET last_login_at = CURRENT_TIMESTAMP,
                login_count =   login_count + 1
            WHERE id = ?
            """,
            (user_id,),
        )
        conn.commit()
    finally:
        conn.close()


"""Preferences queries"""
def get_preferences(user_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT theme, focus_mode, font_size FROM preferences WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row:
            return dict(row)
        return {'theme':'light', 'focus_mode':'standard', 'font_size':'medium'}
    finally:
        conn.close()


def save_preferences(user_id, theme, focus_mode, font_size):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO preferences (user_id, theme, focus_mode, font_size)
            VALUES (?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                theme =         excluded.theme,
                focus_mode =    excluded.focus_mode,
                font_size =     excluded.font_size
            """,
            (user_id, theme, focus_mode, font_size),
        )
        conn.commit()
    finally:
        conn.close()

"""Remember me tokens"""
def create_remember_token(token, user_id, expires_at):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO remember_tokens (token, user_id, expires_at) VALUES (?,?,?)",
            (token, user_id, expires_at)
        )
        conn.commit()
    finally:
        conn.close()

def find_user_by_token(token):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT u.*, rt.expires_at
            FROM remember_tokens rt
            JOIN users u ON u.id = rt.user_id
            WHERE rt.token = ?
            """,
            (token,),
        ).fetchone()

        if not row:
            return None

        expires_at = row['expires_at']
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        if expires_at < now:
            conn.execute("DELETE FROM remember_tokens WHERE token = ?", (token,))
            conn.commit()
            return None

        user = dict(row)
        user.pop('expires_at', None)
        return user
    finally:
        conn.close()

def delete_token(token):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM remember_tokens WHERE token = ?", (token,))
        conn.commit()
    finally:
        conn.close()

def delete_all_tokens_for_user(user_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM remember_tokens WHERE user_id = ?", (user_id,))
        conn.commit()

    finally:
        conn.close()

def count_token_for_user(user_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM remember_tokens WHERE user_id = ?", 
            (user_id,),
        ).fetchone()
        return row['c']
    finally:
        conn.close()

"""Activity logs"""
def log_activity(user_id, action, detail=None):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO activity_log (user_id, action, detail) VALUES (?,?,?)",
            (user_id, action, detail),
        )
        conn.commit()
    finally: 
        conn.close()

def get_recent_activity(user_id, limit=10):
    """Return the latest N activity rows for a user, newest first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT action, detail, timestamp
            FROM activity_log
            WHERE user_id = ?
            ORDER BY timestamp DESC, id DESC
            LIMIT ? 
            """,
            (user_id, limit),
        
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

