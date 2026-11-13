"""Transaction and conflict checks for the narrowly scoped handover importer."""
from pathlib import Path
import os
import unittest
from unittest.mock import patch
from urllib.parse import urlparse, quote
import uuid

import psycopg
from psycopg import sql
from pg_storage import PostgresStore
from scripts.storage_admin import backup
from scripts.import_handover_batch import apply_batch, sample_digest


class HandoverBatchTest(unittest.TestCase):
    def setUp(self):
        self.url = os.environ.get('KEYGUARD_TEST_DATABASE_URL', '')
        parsed = urlparse(self.url)
        if parsed.hostname not in ('127.0.0.1', 'localhost') or parsed.path != '/keyguard_local':
            raise ValueError('Only local test database allowed')
        self.schema = 'kg_handover_' + uuid.uuid4().hex
        with psycopg.connect(self.url, autocommit=True) as connection:
            connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(self.schema)))
        self.addCleanup(self.cleanup_schema)
        self.store = PostgresStore(self.url + '?options=' + quote('-csearch_path=' + self.schema))
        self.store.initialize()
        self.samples = [{'participant_id': 'P01', 'events': [], 'rep': 1}]
        self.store.append_sample('P01', self.samples[0])
        self.digest = sample_digest(self.samples)
        self.snapshot = {'source_sha256': 'fixture-handover',
                         'documents': {'participants.json': {'P01': {'created_at': 'original-value'}}},
                         'attempts': [{'event': 'verify', 'attempt_id': 'fixture'}]}

    def cleanup_schema(self):
        with psycopg.connect(self.url, autocommit=True) as connection:
            connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(self.schema)))

    def test_additive_idempotent_and_preserves_samples(self):
        self.assertEqual(apply_batch(self.store, self.snapshot, self.digest), 'imported')
        self.assertEqual(apply_batch(self.store, self.snapshot, self.digest), 'already_imported')
        self.assertEqual(backup(self.store)['samples'], self.samples)
        self.assertEqual(self.store.attempts(), self.snapshot['attempts'])

    def test_refuses_existing_runtime_state(self):
        self.store.put('accounts.json', {'existing': {'id': 'fixture'}})
        before = backup(self.store)
        with self.assertRaises(ValueError):
            apply_batch(self.store, self.snapshot, self.digest)
        self.assertEqual(backup(self.store), before)

    def test_failed_log_rolls_back_registry_and_batch_marker(self):
        before = backup(self.store)
        with patch.object(self.store, 'append_attempt', side_effect=RuntimeError('Synthetic failure')):
            with self.assertRaises(RuntimeError):
                apply_batch(self.store, self.snapshot, self.digest)
        self.assertEqual(backup(self.store), before)
        self.assertEqual(self.store.summary()['kg_imports'], 0)

    def test_refuses_changed_samples_or_changed_imported_batch(self):
        with self.assertRaises(ValueError):
            apply_batch(self.store, self.snapshot, 'not-the-sample-digest')
        apply_batch(self.store, self.snapshot, self.digest)
        self.store.put('participants.json', {'modified': {}})
        with self.assertRaises(ValueError):
            apply_batch(self.store, self.snapshot, self.digest)
