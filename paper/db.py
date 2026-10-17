"""SQLite persistence. Events are append-only; editions are immutable once committed."""
import json
import sqlite3
from contextlib import contextmanager

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS readers (
  id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
  pw_hash TEXT NOT NULL, persona TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY, reader_id INTEGER NOT NULL REFERENCES readers(id), expires TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY, reader_id INTEGER NOT NULL REFERENCES readers(id), ts TEXT NOT NULL,
  day TEXT NOT NULL, type TEXT NOT NULL, edition_id INTEGER, story_idx INTEGER,
  payload TEXT DEFAULT '{}', simulated INTEGER DEFAULT 0);
CREATE INDEX IF NOT EXISTS ev_reader ON events(reader_id, day);
CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY, url TEXT UNIQUE NOT NULL, domain TEXT NOT NULL, title TEXT NOT NULL,
  description TEXT DEFAULT '', source_time TEXT NOT NULL, day TEXT NOT NULL, image_url TEXT,
  feed_body TEXT, origin TEXT NOT NULL, vec BLOB);
CREATE INDEX IF NOT EXISTS items_day ON items(day);
CREATE TABLE IF NOT EXISTS topics (
  id INTEGER PRIMARY KEY, slug TEXT UNIQUE NOT NULL, label TEXT NOT NULL, description TEXT NOT NULL,
  kind TEXT NOT NULL, owner INTEGER, vec BLOB);
CREATE TABLE IF NOT EXISTS reader_topics (
  reader_id INTEGER NOT NULL, topic_id INTEGER NOT NULL, mode TEXT NOT NULL DEFAULT 'chosen',
  PRIMARY KEY (reader_id, topic_id));
CREATE TABLE IF NOT EXISTS editions (
  id INTEGER PRIMARY KEY, reader_id INTEGER NOT NULL, day TEXT NOT NULL, kind TEXT NOT NULL,
  status TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP, body TEXT NOT NULL,
  pdf_path TEXT, UNIQUE (reader_id, day));
"""


def connect():
    con = sqlite3.connect(config.DB_PATH, timeout=30, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


@contextmanager
def tx():
    con = connect()
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init():
    with tx() as con:
        con.executescript(SCHEMA)


def add_event(con, reader_id, ts, day, type_, edition_id=None, story_idx=None, payload=None, simulated=False):
    con.execute(
        "INSERT INTO events(reader_id, ts, day, type, edition_id, story_idx, payload, simulated) VALUES (?,?,?,?,?,?,?,?)",
        (reader_id, ts, day, type_, edition_id, story_idx, json.dumps(payload or {}), int(simulated)),
    )
