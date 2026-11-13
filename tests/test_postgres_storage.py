"""Real PostgreSQL integration tests; refuse non-loopback/non-test databases."""
from concurrent.futures import ThreadPoolExecutor
import csv
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import socket
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlparse, quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import uuid
import zipfile

import numpy as np
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

from pg_storage import PostgresStore
from scripts.storage_admin import backup, import_snapshot, legacy_snapshot, restore_backup

ROOT = Path(__file__).resolve().parents[1]


def synthetic_samples():
    rng = np.random.default_rng(20261113)
    samples = []
    for _ in range(20):
        t, events = 0., []
        for key in list('.tie5Roanl') + ['Enter']:
            hold = float(rng.uniform(65, 130))
            events += [{'key': key, 'type': 'down', 't': t}, {'key': key, 'type': 'up', 't': t + hold}]
            t += hold + float(rng.uniform(45, 115))
        samples.append(events)
    return samples


class PostgresIntegrationTest(unittest.TestCase):
    def setUp(self):
        url = os.environ.get('KEYGUARD_TEST_DATABASE_URL', '')
        parsed = urlparse(url)
        if parsed.hostname not in ('127.0.0.1', 'localhost') or parsed.path != '/keyguard_local':
            raise RuntimeError('Tests require loopback /keyguard_local database, never production')
        self.schema = 'kg_test_' + uuid.uuid4().hex
        self.admin_url = url
        with psycopg.connect(url, autocommit=True) as connection:
            connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(self.schema)))
        self.url = url + '?options=' + quote('-csearch_path=' + self.schema)
        self.store = PostgresStore(self.url)
        self.store.initialize()
        self.folder = tempfile.TemporaryDirectory(prefix='keyguard-pg-fixture-')
        self.data_dir = Path(self.folder.name) / 'no-files-required'
        self.environment = patch.dict(os.environ, {'DATABASE_URL': self.url, 'KEYGUARD_STORAGE': 'postgres',
              'KEYGUARD_DATA_DIR': str(self.data_dir), 'KEYGUARD_ADMIN_KEY': 'local-test-admin',
              'KEYGUARD_SHOW_OTP': '1', 'KEYGUARD_VERIFY_LIMIT': '100'})
        self.environment.start()
        spec = importlib.util.spec_from_file_location('web_pg_' + self.schema, ROOT / 'app.py')
        self.web = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.web)
        self.client = self.web.app.test_client()
        self.samples = synthetic_samples()

    def tearDown(self):
        self.environment.stop()
        self.folder.cleanup()
        # Only schemas created by this test instance, in explicitly guarded test DB.
        with psycopg.connect(self.admin_url, autocommit=True) as connection:
            connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(self.schema)))

    def enroll(self):
        result = self.client.post('/api/enroll', json={'username': 'Test', 'samples': self.samples})
        self.assertEqual(result.status_code, 200)
        return self.store.get('accounts.json', {})['test']['id']

    def count(self, pid):
        return len(self.store.get('profiles/' + pid + '.json', {})['samples'])

    def rejected(self):
        return [{**e, 't': e['t'] * 12} for e in self.samples[0]]

    def test_real_enrollment_accept_otp_wrong_correct_replay(self):
        pid = self.enroll()
        self.assertEqual(self.count(pid), 20)
        profile = self.store.get('profiles/' + pid + '.json', {})
        sample = next(s for s in self.samples if self.web.verify(profile, s)[1])
        accepted = self.client.post('/api/verify', json={'username': 'TEST', 'events': sample, 'role': 'genuine'})
        self.assertTrue(accepted.json['accepted'])
        self.assertEqual(self.count(pid), 21)
        challenge = self.client.post('/api/verify', json={'username': 'test', 'events': self.rejected(), 'role': 'genuine'}).json
        self.assertTrue(challenge['otp_required'])
        wrong = '000000' if challenge['demo_otp'] != '000000' else '999999'
        payload = {'challenge_id': challenge['challenge_id'], 'otp': wrong}
        self.assertEqual(self.client.post('/api/verify-otp', json=payload).status_code, 401)
        self.assertEqual(self.count(pid), 21)
        self.assertEqual(self.store.get('challenges.json', {})[payload['challenge_id']]['attempts'], 1)
        payload['otp'] = challenge['demo_otp']
        self.assertEqual(self.client.post('/api/verify-otp', json=payload).status_code, 200)
        self.assertEqual(self.count(pid), 22)
        self.assertEqual(self.client.post('/api/verify-otp', json=payload).status_code, 410)
        self.assertEqual(self.count(pid), 22)
        logs = self.store.attempts()
        self.assertEqual([r['otp_result'] for r in logs if r['event'] == 'otp'], ['wrong', 'ok'])
        self.assertFalse(self.data_dir.exists())

    def test_duplicate_and_concurrent_registration_do_not_overwrite(self):
        def register(_):
            with self.web.app.test_client() as client:
                return client.post('/api/enroll', json={'username': 'Test', 'samples': self.samples}).status_code
        with ThreadPoolExecutor(max_workers=2) as executor:
            self.assertEqual(sorted(executor.map(register, range(2))), [200, 409])
        accounts = self.store.get('accounts.json', {})
        self.assertEqual(len(accounts), 1)
        self.assertEqual(self.count(accounts['test']['id']), 20)

    def test_concurrent_id_allocation_and_sample_reps(self):
        def get_id(_):
            with self.web.app.test_client() as client:
                return client.get('/api/get-id').json['participant_id']
        with ThreadPoolExecutor(max_workers=8) as executor:
            ids = list(executor.map(get_id, range(8)))
        self.assertEqual(len(set(ids)), 8)
        pid = ids[0]
        def submit(_):
            with self.web.app.test_client() as client:
                response = client.post('/api/submit-sample', json={'participant_id': pid, 'session': 1, 'events': self.samples[0]})
                self.assertEqual(response.status_code, 200)
                return response.json['rep']
        with ThreadPoolExecutor(max_workers=8) as executor:
            self.assertEqual(sorted(executor.map(submit, range(8))), list(range(1, 9)))
        self.assertEqual(self.client.get('/api/participant/' + pid).json['sessions']['1'], 8)
        self.assertEqual(len(self.store.records(pid)), 8)

    def test_atomic_rollback_if_logging_fails_after_profile_update(self):
        pid = self.enroll()
        profile = self.store.get('profiles/' + pid + '.json', {})
        sample = next(s for s in self.samples if self.web.verify(profile, s)[1])
        with patch.object(self.web.PG, 'append_attempt', side_effect=RuntimeError('Synthetic log failure')):
            response = self.client.post('/api/verify', json={'username': 'test', 'events': sample})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(self.count(pid), 20)
        self.assertEqual(self.store.attempts(), [])

    def test_otp_locked_attempts_persist_even_on_429(self):
        pid = self.enroll()
        challenge = self.client.post('/api/verify', json={'username': 'test', 'events': self.rejected()}).json
        wrong = '000000' if challenge['demo_otp'] != '000000' else '999999'
        responses = [self.client.post('/api/verify-otp', json={'challenge_id': challenge['challenge_id'], 'otp': wrong}).status_code for _ in range(3)]
        self.assertEqual(responses, [401, 401, 429])
        self.assertNotIn(challenge['challenge_id'], self.store.get('challenges.json', {}))
        self.assertEqual(self.count(pid), 20)
        self.assertEqual([r['otp_result'] for r in self.store.attempts() if r['event'] == 'otp'], ['wrong', 'wrong', 'locked'])

    def test_state_and_pending_otp_survive_new_python_process(self):
        pid = self.enroll()
        challenge = self.client.post('/api/verify', json={'username': 'test', 'events': self.rejected()}).json
        script = """import json,sys
import app
c=app.app.test_client()
data=json.loads(sys.stdin.read())
r=c.post('/api/verify-otp',json=data)
assert r.status_code==200
print('NEW_PROCESS_OTP_OK')
"""
        run = subprocess.run([sys.executable, '-c', script], cwd=ROOT, input=json.dumps({
            'challenge_id': challenge['challenge_id'], 'otp': challenge['demo_otp']}),
            capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(run.returncode, 0, run.stdout)  # Never output a URL/secret error trace.
        self.assertIn('NEW_PROCESS_OTP_OK', run.stdout)
        self.assertEqual(self.count(pid), 21)
        self.assertEqual(len(self.store.attempts()), 2)

    def test_export_stats_exclude_profiles_names_challenge_hashes(self):
        self.enroll()
        pid = self.client.get('/api/get-id').json['participant_id']
        self.client.post('/api/submit-sample', json={'participant_id': pid, 'session': 1, 'events': self.samples[0]})
        self.client.post('/api/verify', json={'username': 'test', 'events': self.rejected(), 'role': 'genuine'})
        self.assertEqual(self.client.get('/admin/export').status_code, 404)
        export = self.client.get('/admin/export', headers={'X-Admin-Key': 'local-test-admin'})
        self.assertEqual(export.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(export.data)) as z:
            self.assertEqual(set(z.namelist()), {'collected/' + pid + '.jsonl', 'participants.json', 'attempts.csv'})
            self.assertEqual(len(z.read('collected/' + pid + '.jsonl').splitlines()), 1)
            rows = list(csv.DictReader(io.StringIO(z.read('attempts.csv').decode())))
            self.assertEqual(len(rows), 1)
            self.assertNotIn('username', rows[0])
        stats = self.client.get('/admin/stats', headers={'X-Admin-Key': 'local-test-admin'}).json
        self.assertEqual(stats['participants'][pid]['samples'], 1)
        self.assertEqual(stats['attempts']['total'], 1)

    def test_invalid_sample_unknown_id_and_bool_session_do_not_write(self):
        pid = self.client.get('/api/get-id').json['participant_id']
        for participant, session, events in [(pid, True, self.samples[0]), ('P99', 1, self.samples[0]), (pid, 1, [])]:
            result = self.client.post('/api/submit-sample', json={'participant_id': participant, 'session': session, 'events': events})
            self.assertIn(result.status_code, (400, 404))
        self.assertEqual(self.store.summary()['kg_samples'], 0)

    def test_import_preserves_duplicates_and_is_idempotent(self):
        source = Path(self.folder.name) / 'legacy'
        (source / 'collected').mkdir(parents=True)
        row = {'participant_id': 'P10', 'session': 1, 'rep': 29, 'events': self.samples[0]}
        (source / 'collected/P10.jsonl').write_text(json.dumps(row) + '\n' + json.dumps(row) + '\n')
        snapshot = legacy_snapshot(source)
        self.assertEqual(self.store.summary()['kg_samples'], 0)  # Parsing/dry-run did not write.
        self.assertEqual(import_snapshot(self.store, snapshot), 'imported')
        self.assertEqual(import_snapshot(self.store, snapshot), 'already_imported')
        self.assertEqual(self.store.records('P10'), [row, row])
        changed = {**snapshot, 'source_sha256': 'different'}
        with self.assertRaises(RuntimeError):
            import_snapshot(self.store, changed)
        self.assertEqual(self.store.summary()['kg_samples'], 2)

    def test_private_backup_contains_account_profiles_and_safe_restore_to_empty_target(self):
        self.enroll()
        saved = backup(self.store)
        self.assertIn('accounts.json', saved['documents'])
        self.assertTrue(any(k.startswith('profiles/') for k in saved['documents']))
        with self.assertRaises(RuntimeError):
            restore_backup(self.store, saved)
        # New empty test-only schema: simulate restore in a fresh database namespace.
        other = self.schema + '_restore'
        with psycopg.connect(self.admin_url, autocommit=True) as connection:
            connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(other)))
        try:
            store = PostgresStore(self.admin_url + '?options=' + quote('-csearch_path=' + other))
            store.initialize()
            self.assertEqual(restore_backup(store, saved), 'imported')
            self.assertEqual(backup(store), saved)
            self.assertEqual(restore_backup(store, saved), 'already_imported')
        finally:
            with psycopg.connect(self.admin_url, autocommit=True) as connection:
                connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(other)))

    def test_nested_transaction_rollback_releases_lock_and_connection(self):
        with self.assertRaises(RuntimeError):
            with self.store.transaction():
                self.store.put('accounts.json', {'partial': {}})
                raise RuntimeError('Synthetic abort')
        self.assertEqual(self.store.get('accounts.json', {}), {})
        self.store.put('accounts.json', {'committed': {}})
        self.assertIn('committed', PostgresStore(self.url).get('accounts.json', {}))

    def test_missing_database_url_or_unavailable_db_never_falls_back_to_files(self):
        with self.assertRaises(ValueError):
            PostgresStore(None)
        # local endpoint with no listener; failure must not make any data directory.
        store = PostgresStore('postgresql://test:test@127.0.0.1:1/keyguard_local')
        with self.assertRaises(RuntimeError):
            store.check_schema()
        self.assertFalse(self.data_dir.exists())

    def test_otp_update_failure_rolls_back_consumed_challenge(self):
        pid = self.enroll()
        challenge = self.client.post('/api/verify', json={'username': 'test', 'events': self.rejected()}).json
        with patch.object(self.web, 'apply_update', side_effect=RuntimeError('Synthetic update failure')):
            response = self.client.post('/api/verify-otp', json={'challenge_id': challenge['challenge_id'], 'otp': challenge['demo_otp']})
        self.assertEqual(response.status_code, 500)
        self.assertIn(challenge['challenge_id'], self.store.get('challenges.json', {}))
        self.assertEqual(self.count(pid), 20)
        self.assertEqual(len(self.store.attempts()), 1)

    def test_import_failure_rolls_back_entire_batch(self):
        snapshot = {'source_sha256': 'synthetic-bad', 'documents': {'participants.json': {'P01': {}}},
                    'samples': [{'participant_id': 'P01', 'bad': float('nan')}], 'attempts': []}
        with self.assertRaises(Exception):
            import_snapshot(self.store, snapshot)
        self.assertEqual(self.store.summary(), {'kg_documents': 0, 'kg_samples': 0, 'kg_attempts': 0, 'kg_imports': 0})

    def test_file_backend_remains_usable_without_database(self):
        with patch.dict(os.environ, {'KEYGUARD_STORAGE': 'file', 'DATABASE_URL': ''}):
            spec = importlib.util.spec_from_file_location('web_file_' + self.schema, ROOT / 'app.py')
            web = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(web)
            client = web.app.test_client()
            self.assertIsNone(web.PG)
            pid = client.get('/api/get-id').json['participant_id']
            response = client.post('/api/submit-sample', json={'participant_id': pid, 'session': 1, 'events': self.samples[0]})
            self.assertEqual(response.status_code, 200)
            self.assertTrue((self.data_dir / 'collected' / (pid + '.jsonl')).is_file())
            self.assertEqual(client.get('/api/participant/' + pid).json['sessions']['1'], 1)

    def test_real_http_gunicorn_two_workers_and_application_restart(self):
        if sys.platform == 'win32':
            self.fail('Run this integration suite on Linux for Gunicorn, not a mock substitute')
        with socket.socket() as available:
            available.bind(('127.0.0.1', 0))
            port = available.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        process = None

        def start():
            nonlocal process
            process = subprocess.Popen([sys.executable, '-m', 'gunicorn', 'app:app', '--bind', f'127.0.0.1:{port}',
                                        '--workers', '2', '--timeout', '30'], cwd=ROOT,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError('Gunicorn startup failed')
                try:
                    with urlopen(base + '/login', timeout=1) as response:
                        if response.status == 200:
                            return
                except (URLError, TimeoutError):
                    time.sleep(.05)
            raise RuntimeError('Gunicorn readiness timed out')

        def stop():
            if process and process.poll() is None:
                process.terminate()
                process.wait(timeout=10)

        def request(route, value=None):
            body = None if value is None else json.dumps(value).encode()
            req = Request(base + route, data=body, headers={'Content-Type': 'application/json'})
            try:
                with urlopen(req, timeout=10) as response:
                    return response.status, json.load(response)
            except HTTPError as response:
                return response.code, json.load(response)

        try:
            start()
            self.assertEqual(request('/api/enroll', {'username': 'HttpTest', 'samples': self.samples})[0], 200)
            pid = self.store.get('accounts.json', {})['httptest']['id']
            profile = self.store.get('profiles/' + pid + '.json', {})
            accepted = next(s for s in self.samples if self.web.verify(profile, s)[1])
            self.assertTrue(request('/api/verify', {'username': 'HttpTest', 'events': accepted})[1]['accepted'])
            self.assertEqual(self.count(pid), 21)
            challenge = request('/api/verify', {'username': 'HttpTest', 'events': self.rejected()})[1]
            participant = request('/api/get-id')[1]['participant_id']
            self.assertEqual(request('/api/submit-sample', {'participant_id': participant, 'session': 1, 'events': self.samples[0]})[0], 200)
            stop()
            self.assertFalse(self.data_dir.exists())
            start()
            self.assertFalse(request('/api/check-username?username=HttpTest')[1]['available'])
            self.assertEqual(request('/api/participant/' + participant)[1]['sessions']['1'], 1)
            self.assertEqual(request('/api/verify-otp', {'challenge_id': challenge['challenge_id'], 'otp': challenge['demo_otp']})[0], 200)
            self.assertEqual(self.count(pid), 22)
            self.assertEqual(request('/api/verify-otp', {'challenge_id': challenge['challenge_id'], 'otp': challenge['demo_otp']})[0], 410)
        finally:
            stop()


if __name__ == '__main__':
    unittest.main()
