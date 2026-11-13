"""PostgreSQL persistence for the existing web JSON contracts, not model code."""
from contextlib import contextmanager
from contextvars import ContextVar
import json

import psycopg
from psycopg.types.json import Jsonb

LOCK_ID = 7319626041
SCHEMA_VERSION = 1

DDL = """
CREATE TABLE IF NOT EXISTS kg_schema (version integer PRIMARY KEY);
INSERT INTO kg_schema(version) VALUES (1) ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS kg_documents (
  name text PRIMARY KEY, payload jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS kg_samples (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  participant_id text NOT NULL, payload jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS kg_samples_participant ON kg_samples(participant_id,id);
CREATE TABLE IF NOT EXISTS kg_attempts (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, payload jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS kg_imports (
  source_sha256 text PRIMARY KEY, imported_at timestamptz NOT NULL DEFAULT now()
);
"""


class PostgresStore:
    def __init__(self, url):
        if not url or not url.startswith(('postgresql://', 'postgres://')):
            raise ValueError('PostgreSQL DATABASE_URL is required')
        self._url = url
        self._connection = ContextVar('keyguard_pg_connection', default=None)

    @contextmanager
    def transaction(self):
        current = self._connection.get()
        if current is not None:
            yield current
            return
        # No connection survives a request, fork, thread or restart.
        try:
            connection = psycopg.connect(self._url, connect_timeout=5)
        except psycopg.Error:
            raise RuntimeError('PostgreSQL unavailable; no file fallback') from None
        token = self._connection.set(connection)
        try:
            with connection:
                connection.execute("SET LOCAL lock_timeout = '10s'")
                connection.execute("SET LOCAL statement_timeout = '30s'")
                # Coarse application lock preserves existing read-modify-write JSON
                # semantics across workers. Intentionally favors correctness over throughput.
                connection.execute('SELECT pg_advisory_xact_lock(%s)', (LOCK_ID,))
                yield connection
        finally:
            self._connection.reset(token)

    def initialize(self):
        with self.transaction() as connection:
            exists = connection.execute("SELECT to_regclass('kg_schema')").fetchone()[0]
            if exists:
                versions = connection.execute('SELECT version FROM kg_schema').fetchall()
                if versions != [(SCHEMA_VERSION,)]:
                    raise RuntimeError('Unsupported database schema; manual migration required')
            connection.execute(DDL)

    def check_schema(self):
        try:
            with self.transaction() as connection:
                versions = connection.execute('SELECT version FROM kg_schema').fetchall()
                if versions != [(SCHEMA_VERSION,)]:
                    raise RuntimeError('Unsupported database schema')
                for table in ('kg_documents', 'kg_samples', 'kg_attempts', 'kg_imports'):
                    if connection.execute('SELECT to_regclass(%s)', (table,)).fetchone()[0] is None:
                        raise RuntimeError('Incomplete PostgreSQL schema')
        except psycopg.Error:
            raise RuntimeError('PostgreSQL schema not ready; run storage_admin.py init') from None

    def get(self, name, default):
        with self.transaction() as connection:
            row = connection.execute('SELECT payload FROM kg_documents WHERE name=%s', (name,)).fetchone()
            return row[0] if row else default

    def put(self, name, value):
        with self.transaction() as connection:
            connection.execute('INSERT INTO kg_documents(name,payload) VALUES (%s,%s) '
                               'ON CONFLICT(name) DO UPDATE SET payload=EXCLUDED.payload', (name, Jsonb(value)))

    def records(self, pid):
        with self.transaction() as connection:
            return [r[0] for r in connection.execute(
                'SELECT payload FROM kg_samples WHERE participant_id=%s ORDER BY id', (pid,))]

    def participant_ids(self):
        with self.transaction() as connection:
            return {r[0] for r in connection.execute('SELECT DISTINCT participant_id FROM kg_samples')}

    def append_sample(self, pid, record):
        with self.transaction() as connection:
            connection.execute('INSERT INTO kg_samples(participant_id,payload) VALUES (%s,%s)', (pid, Jsonb(record)))

    def append_attempt(self, record):
        # Match CSV contract: missing fields remain empty, numeric values stored as text.
        with self.transaction() as connection:
            connection.execute('INSERT INTO kg_attempts(payload) VALUES (%s)', (Jsonb(record),))

    def attempts(self):
        with self.transaction() as connection:
            return [r[0] for r in connection.execute('SELECT payload FROM kg_attempts ORDER BY id')]

    def summary(self):
        with self.transaction() as connection:
            return {table: connection.execute('SELECT count(*) FROM ' + table).fetchone()[0]
                    for table in ('kg_documents', 'kg_samples', 'kg_attempts', 'kg_imports')}
