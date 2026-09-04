"""
Storage layer for the AI Registration Assistant.

Provides functions to save and load registration records.
Records are persisted to a PostgreSQL database when a DATABASE_URL
environment variable is available (e.g. on Render), and fall back to
a local JSON file otherwise (e.g. local development / testing).

This keeps the chatbot and admin logic unchanged regardless of backend.
"""

import json
import os

import psycopg2
import psycopg2.extras

# -------------------------------------------------------------------
# Locations
# -------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, 'registrations.json')

DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()

# Column definitions for the registrations table.
COLS = ['name', 'email', 'field', 'experience', 'registered_at']


def _connect():
    """Connect to PostgreSQL using the DATABASE_URL."""
    return psycopg2.connect(DATABASE_URL)


def _init_db(conn):
    """Create the registrations table if it does not already exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id SERIAL PRIMARY KEY,
                name TEXT,
                email TEXT,
                field TEXT,
                experience TEXT,
                registered_at TEXT
            )
        """)
    conn.commit()


def load_registrations():
    """
    Return a list of registration records (newest first for admin display).
    """
    # Postgres backend
    if DATABASE_URL:
        try:
            conn = _connect()
            _init_db(conn)
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT name, email, field, experience, registered_at "
                    "FROM registrations ORDER BY id"
                )
                rows = cur.fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []

    # JSON fallback for local/testing
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_registration(record):
    """Insert a single registration record into the database."""
    if DATABASE_URL:
        try:
            conn = _connect()
            _init_db(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO registrations (name, email, field, experience, registered_at) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (
                        record.get('name'),
                        record.get('email'),
                        record.get('field'),
                        record.get('experience'),
                        record.get('registered_at'),
                    ),
                )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    # JSON fallback for local/testing
    records = load_registrations()
    records.append(record)
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
    return True


def delete_registration(index):
    """
    Delete a registration by its position in the ordered list returned by
    load_registrations(). Returns True on success, False otherwise.
    """
    records = load_registrations()
    if not (0 <= index < len(records)):
        return False

    if DATABASE_URL:
        # Find the actual row id by re-querying in the same order.
        try:
            conn = _connect()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id FROM registrations ORDER BY id")
                ids = [r['id'] for r in cur.fetchall()]
            if 0 <= index < len(ids):
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM registrations WHERE id = %s", (ids[index],))
                conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    # JSON fallback
    records.pop(index)
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
    return True