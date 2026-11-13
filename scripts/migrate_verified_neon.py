"""Import only the audited 601-row export to the already linked Neon database."""
import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlparse
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import psycopg
from pg_storage import PostgresStore
from scripts.storage_admin import backup, import_snapshot, legacy_snapshot

ARCHIVE_SHA = '9e195b9338f4d5f2e73341349b5fcc97a6525dce7c9a3016cb857fe11f6779df'
SOURCE_SHA = '74ca5ac99cff345fc881427a542f009369224f2ed856428ab3d0024136a15e69'


def neon_url():
    url = os.environ.get('DATABASE_URL_UNPOOLED', '')
    parsed = urlparse(url)
    if (not parsed.hostname or not parsed.hostname.endswith('.neon.tech')
            or parse_qs(parsed.query).get('sslmode', [''])[0] not in ('require', 'verify-ca', 'verify-full')
            or parse_qs(parsed.query).get('options')):
        raise ValueError('Expected direct Neon TLS configuration without schema override')
    return url


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    archive_raw = args.archive.read_bytes()
    if hashlib.sha256(archive_raw).hexdigest() != ARCHIVE_SHA:
        raise ValueError('Archive hash differs from reviewed source')
    snapshot = legacy_snapshot(args.source)
    if snapshot['source_sha256'] != SOURCE_SHA or len(snapshot['samples']) != 601:
        raise ValueError('Source differs from reviewed snapshot')
    if snapshot['documents'] or snapshot['attempts']:
        raise ValueError('Unexpected documents or logs; review before import')
    with zipfile.ZipFile(io.BytesIO(archive_raw)) as archive:
        assert archive.testzip() is None
        names = [n for n in archive.namelist() if not n.endswith('/')]
        assert set(names) == set(snapshot['source_file_sha256'])
        assert all(hashlib.sha256(archive.read(n)).hexdigest() == snapshot['source_file_sha256'][n] for n in names)
    print(json.dumps({'phase': 'source_verified', 'samples': 601, 'files': 15,
                      'source_sha256': SOURCE_SHA, 'apply': args.apply}), flush=True)
    if not args.apply:
        return
    url = neon_url()
    args.out.mkdir(parents=True, exist_ok=False)
    with psycopg.connect(url, connect_timeout=15) as connection:
        assert connection.pgconn.ssl_in_use
        # Refuse creating objects into an application namespace with unrelated tables.
        existing = {r[0] for r in connection.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='public'")}
        allowed = {'kg_schema', 'kg_documents', 'kg_samples', 'kg_attempts', 'kg_imports'}
        if existing - allowed:
            raise ValueError('Unrelated public tables found; review target before initializing')
    store = PostgresStore(url)
    store.initialize()
    store.check_schema()
    before = store.summary()
    before_payload = backup(store)
    with (args.out / 'before.private-backup.json').open('x', encoding='utf-8') as stream:
        json.dump(before_payload, stream, allow_nan=False)
    print(json.dumps({'phase': 'schema_ready', 'before': before}), flush=True)
    outcome = import_snapshot(store, snapshot)
    assert import_snapshot(store, snapshot) == 'already_imported'
    expected = {}
    for row in snapshot['samples']:
        expected.setdefault(row['participant_id'], []).append(row)
    # All comparisons share one read transaction and one connection.
    with store.transaction():
        assert store.participant_ids() == set(expected)
        assert all(store.records(pid) == rows for pid, rows in expected.items())
        payload = backup(store)
        after = store.summary()
    assert after == {'kg_documents': 0, 'kg_samples': 601, 'kg_attempts': 0, 'kg_imports': 1}
    with (args.out / 'after.private-backup.json').open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, ensure_ascii=False, allow_nan=False)
    os.environ.update(DATABASE_URL=url, KEYGUARD_STORAGE='postgres',
                      KEYGUARD_ADMIN_KEY='migration-readonly-export-check',
                      KEYGUARD_DATA_DIR=str(args.out / 'unused-file-backend'))
    spec = importlib.util.spec_from_file_location('neon_migration_web', ROOT / 'app.py')
    web = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(web)
    client = web.app.test_client()
    response = client.get('/admin/export', headers={'X-Admin-Key': 'migration-readonly-export-check'})
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
        actual = {n: [json.loads(line) for line in archive.read(n).decode('utf-8-sig').splitlines() if line.strip()]
                  for n in archive.namelist() if n.endswith('.jsonl')}
    assert actual == {'collected/' + pid + '.jsonl': rows for pid, rows in expected.items()}
    assert store.summary() == after
    report = {'date': '2026-11-13', 'project_id': 'bitter-resonance-81924970',
              'schema': 'public', 'source_archive_sha256': ARCHIVE_SHA,
              'source_snapshot_sha256': SOURCE_SHA, 'samples': 601, 'participants': 15,
              'client_tls': True, 'import_result': outcome, 'before': before, 'after': after,
              'checks': {'source_zip_hash_crc_and_files': True, 'records_and_order_equal': True,
                         'repeat_import_idempotent': True, 'http_export_semantically_equal': True,
                         'before_and_after_private_backups_saved': True, 'no_file_backend_writes': not (args.out / 'unused-file-backend').exists()},
              'accounts_profiles_attempts_recovered': False,
              'limitations': ['Historical collected samples only; absent accounts/profiles/logs not recreated',
                              'JSONB preserves values and order, not original JSONL bytes',
                              'Private backups stored locally; off-site backup not verified',
                              'Render still file backend; not cut over or deployed'],
              'render_configuration_changed': False, 'deployed': False}
    (args.out / 'validation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'phase': 'import_and_export_verified', 'after': after, 'checks': report['checks']}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Neon migration stopped (' + type(error).__name__ + '); credentials withheld', file=sys.stderr)
        raise SystemExit(1)
