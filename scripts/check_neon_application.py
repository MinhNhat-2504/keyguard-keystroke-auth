"""Run selected existing integration cases on disposable Neon schemas only."""
import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import psycopg
from psycopg import sql
from pg_storage import PostgresStore
from scripts.migrate_verified_neon import neon_url
from scripts.storage_admin import backup, restore_backup

spec = importlib.util.spec_from_file_location('local_cases', ROOT / 'tests/test_postgres_storage.py')
cases = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cases)


def scoped_url(url, schema):
    parsed = urlparse(url)
    query = [(k, v) for k, v in parse_qsl(parsed.query) if k != 'options']
    return urlunparse(parsed._replace(query=urlencode(query + [('options', '-csearch_path=' + schema)])))


def remove_schema(url, schema):
    if not schema.startswith('kg_neon_check_') or not schema.removeprefix('kg_neon_check_').isalnum():
        raise ValueError('Refuse dropping any schema not created by this runner')
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


class NeonApplicationCases(cases.PostgresIntegrationTest):
    def setUp(self):
        self.admin_url = neon_url()
        self.schema = 'kg_neon_check_' + uuid.uuid4().hex
        with psycopg.connect(self.admin_url, autocommit=True) as connection:
            connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(self.schema)))
        self.addCleanup(remove_schema, self.admin_url, self.schema)
        self.url = scoped_url(self.admin_url, self.schema)
        self.store = PostgresStore(self.url)
        self.store.initialize()
        self.folder = tempfile.TemporaryDirectory(prefix='keyguard-neon-check-')
        self.addCleanup(self.folder.cleanup)
        self.data_dir = Path(self.folder.name) / 'no-files-required'
        self.environment = patch.dict(os.environ, {
            'DATABASE_URL': self.url, 'KEYGUARD_STORAGE': 'postgres',
            'KEYGUARD_DATA_DIR': str(self.data_dir), 'KEYGUARD_ADMIN_KEY': 'synthetic-neon-check',
            'KEYGUARD_SHOW_OTP': '1', 'KEYGUARD_VERIFY_LIMIT': '100'})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        spec = importlib.util.spec_from_file_location('web_' + self.schema, ROOT / 'app.py')
        self.web = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.web)
        self.client = self.web.app.test_client()
        self.samples = cases.synthetic_samples()

    def tearDown(self):
        # addCleanup also runs when setup or the case fails.
        pass


SELECTED = [
    'test_real_enrollment_accept_otp_wrong_correct_replay',
    'test_concurrent_id_allocation_and_sample_reps',
    'test_atomic_rollback_if_logging_fails_after_profile_update',
    'test_otp_locked_attempts_persist_even_on_429',
    'test_real_http_gunicorn_two_workers_and_application_restart',
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    url = neon_url()
    public = PostgresStore(url)
    before = backup(public)
    saved = json.loads(args.backup.read_text(encoding='utf-8'))
    if before != saved or len(saved['samples']) != 601:
        raise ValueError('Public data changed since migration; review before running checks')
    # The app's default URL is pooled; migration/isolated-schema checks use direct.
    pooled = PostgresStore(os.environ['DATABASE_URL'])
    assert backup(pooled) == before
    payload_hash = hashlib.sha256(json.dumps(before, sort_keys=True, allow_nan=False).encode()).hexdigest()
    suite = unittest.TestSuite(NeonApplicationCases(name) for name in SELECTED)
    # Case failures may contain sensitive request details; keep them out of console.
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=0).run(suite)
    print(json.dumps({'phase': 'application_cases', 'run': result.testsRun,
                      'failures': len(result.failures), 'errors': len(result.errors)}), flush=True)
    report = {'date': '2026-11-13', 'project_id': 'bitter-resonance-81924970',
              'backend': 'Real Neon over TLS; app processes in local Linux Docker',
              'cases': SELECTED, 'tests': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors),
              'failed_case_names': [str(t) for t, _ in result.failures + result.errors],
              'historical_payload_sha256': payload_hash,
              'pooled_and_direct_read_same_data': True,
              'synthetic_schemas_cleaned': True,
              'render_configuration_changed': False, 'deployed': False}
    restore_schema = 'kg_neon_check_' + uuid.uuid4().hex
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(restore_schema)))
    try:
        restored = PostgresStore(scoped_url(url, restore_schema))
        restored.initialize()
        assert restore_backup(restored, saved) == 'imported'
        assert backup(restored) == saved
        assert restore_backup(restored, saved) == 'already_imported'
        report['backup_restore_601_equal_and_idempotent'] = True
    finally:
        remove_schema(url, restore_schema)
    assert backup(public) == before
    with psycopg.connect(url) as connection:
        leftovers = connection.execute("SELECT count(*) FROM information_schema.schemata WHERE schema_name LIKE 'kg_neon_check_%'").fetchone()[0]
    report['synthetic_schemas_remaining'] = leftovers
    report['public_data_unchanged_after_tests'] = True
    report['checks_passed'] = result.wasSuccessful() and leftovers == 0
    args.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'phase': 'backup_restore_and_isolation', 'public_unchanged': True,
                      'schemas_remaining': leftovers, 'checks_passed': report['checks_passed']}), flush=True)
    return 0 if report['checks_passed'] else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print('Neon application check stopped (' + type(error).__name__ + '); credentials withheld', file=sys.stderr)
        raise SystemExit(1)
