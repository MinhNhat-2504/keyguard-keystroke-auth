"""Rehearse a saved export on isolated local schemas; never a cloud migration."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import psycopg
from psycopg import sql
from pg_storage import PostgresStore
from scripts.storage_admin import backup, import_snapshot, legacy_snapshot, restore_backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    url = os.environ.get('KEYGUARD_TEST_DATABASE_URL', '')
    parsed = urlparse(url)
    if parsed.hostname not in ('localhost', '127.0.0.1') or parsed.path != '/keyguard_local':
        raise ValueError('Only loopback /keyguard_local is allowed; never production')
    archive_bytes = args.archive.read_bytes()
    archive_hash = hashlib.sha256(archive_bytes).hexdigest()
    if archive_hash != args.expected_sha256:
        raise ValueError('Archive changed; stop and review the source')
    args.out.mkdir(parents=True, exist_ok=False)
    source = args.out / 'source'
    source.mkdir()
    # Keep a byte-exact original alongside the semantic JSONB round-trip.
    (args.out / 'original-export.zip').write_bytes(archive_bytes)
    member_hashes = {}
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP CRC failed')
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            name = entry.filename
            if not re.fullmatch(r'collected/P\d{2,4}\.jsonl', name):
                raise ValueError('Unexpected export member; review rather than auto-import')
            if name in member_hashes or entry.file_size > 20_000_000:
                raise ValueError('Duplicate or oversized member')
            raw = archive.read(entry)
            member_hashes[name] = hashlib.sha256(raw).hexdigest()
            path = source / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(raw)
    snapshot = legacy_snapshot(source)
    if len(snapshot['samples']) != 601 or len(member_hashes) != 15:
        raise ValueError('This rehearsal expects the previously audited 601-row/15-file export')
    schemas = []
    try:
        stores = []
        for _ in range(2):
            schema = 'kg_rehearsal_' + uuid.uuid4().hex
            with psycopg.connect(url, autocommit=True) as connection:
                connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
            schemas.append(schema)
            query = [(k, v) for k, v in parse_qsl(parsed.query) if k != 'options']
            scoped = urlunparse(parsed._replace(query=urlencode(query + [('options', '-csearch_path=' + schema)])))
            store = PostgresStore(scoped)
            store.initialize()
            stores.append((store, scoped))
        store, scoped_url = stores[0]
        assert import_snapshot(store, snapshot) == 'imported'
        assert import_snapshot(store, snapshot) == 'already_imported'
        expected = {}
        for row in snapshot['samples']:
            expected.setdefault(row['participant_id'], []).append(row)
        assert all(store.records(pid) == rows for pid, rows in expected.items())
        payload = backup(store)
        with (args.out / 'roundtrip.private-backup.json').open('x', encoding='utf-8') as stream:
            json.dump(payload, stream, ensure_ascii=False, allow_nan=False)
        assert restore_backup(stores[1][0], payload) == 'imported'
        assert backup(stores[1][0]) == payload
        os.environ.update(DATABASE_URL=scoped_url, KEYGUARD_STORAGE='postgres',
                          KEYGUARD_ADMIN_KEY='local-rehearsal-only',
                          KEYGUARD_DATA_DIR=str(args.out / 'unused-file-backend'))
        spec = importlib.util.spec_from_file_location('rehearsal_web', ROOT / 'app.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        response = module.app.test_client().get('/admin/export', headers={'X-Admin-Key': 'local-rehearsal-only'})
        assert response.status_code == 200
        with zipfile.ZipFile(io.BytesIO(response.data)) as exported:
            samples = {n: [json.loads(line) for line in exported.read(n).decode('utf-8-sig').splitlines() if line.strip()]
                       for n in exported.namelist() if n.endswith('.jsonl')}
        assert samples == {'collected/' + pid + '.jsonl': rows for pid, rows in expected.items()}
        counts = Counter((r.get('participant_id'), r.get('session'), r.get('rep')) for r in snapshot['samples'])
        report = {
            'date': '2026-11-13', 'provider_selected': 'Neon Free; not provisioned or connected',
            'source_archive_sha256': archive_hash, 'source_member_sha256': member_hashes,
            'source_snapshot_sha256': snapshot['source_sha256'],
            'samples': len(snapshot['samples']), 'participants': len(expected),
            'duplicate_keys_preserved': sum(n - 1 for n in counts.values() if n > 1),
            'accounts_profiles_attempts_available': False,
            'checks': {'original_zip_byte_exact': True, 'zip_crc': True,
                       'import_records_equal_in_order': True, 'repeat_import_idempotent': True,
                       'private_backup_restore_equal': True, 'http_export_rows_equal_in_order': True},
            'limitations': ['JSONB round-trip preserves values, not original JSONL bytes',
                            '601 collected rows only; no accounts, profiles or attempt logs in this source',
                            'Local rehearsal only; no cloud upload, production write or deployment',
                            'Local backup copies are on the same disk; no off-site backup verified'],
        }
    finally:
        for schema in schemas:
            with psycopg.connect(url, autocommit=True) as connection:
                connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
    report['temporary_schemas_removed'] = True
    (args.out / 'validation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'samples': report['samples'], 'participants': report['participants'],
                      'checks': report['checks'], 'temporary_schemas_removed': True}))


if __name__ == '__main__':
    main()
