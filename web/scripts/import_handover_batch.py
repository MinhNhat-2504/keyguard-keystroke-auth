"""Add the reviewed registry/9-row boundary-test handover without merging live CSVs."""
import argparse
import hashlib
import io
import importlib.util
import json
import os
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pg_storage import PostgresStore
from scripts.migrate_verified_neon import neon_url
from scripts.storage_admin import backup, legacy_snapshot

FILE_HASHES = {
    'participants.json': 'e77a365b833a5103e065b80512d97090e76b02f31a0111ba9bf2069775dbcd89',
    'attempts.csv': 'b5b214cf5d45cec9c27282aabd9ae6cf306c1e2fc655c89269accd494d5377a7',
}


def sample_digest(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, allow_nan=False).encode()).hexdigest()


def apply_batch(store, snapshot, expected_samples_digest):
    """Strict, atomic additive operation against the known pre-cutover state."""
    with store.transaction() as connection:
        current = backup(store)
        if sample_digest(current['samples']) != expected_samples_digest:
            raise ValueError('Samples changed; refuse applying the handover')
        seen = connection.execute('SELECT 1 FROM kg_imports WHERE source_sha256=%s',
                                  (snapshot['source_sha256'],)).fetchone()
        if seen:
            if current['documents'] != snapshot['documents'] or current['attempts'] != snapshot['attempts']:
                raise ValueError('Previously imported batch differs from current state; review')
            return 'already_imported'
        if current['documents'] or current['attempts']:
            raise ValueError('Registry/accounts/logs already exist; refuse merge or overwrite')
        for name, value in snapshot['documents'].items():
            store.put(name, value)
        for row in snapshot['attempts']:
            store.append_attempt(row)
        connection.execute('INSERT INTO kg_imports(source_sha256) VALUES (%s)', (snapshot['source_sha256'],))
    return 'imported'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--baseline-backup', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    snapshot = legacy_snapshot(args.source)
    if (snapshot['source_file_sha256'] != FILE_HASHES or snapshot['samples']
            or set(snapshot['documents']) != {'participants.json'} or len(snapshot['attempts']) != 9
            or set(snapshot['documents']['participants.json']) != {f'P{i:02}' for i in range(1, 16)}):
        raise ValueError('Source differs from reviewed handover')
    baseline = json.loads(args.baseline_backup.read_text(encoding='utf-8'))
    if len(baseline['samples']) != 601 or baseline['documents'] or baseline['attempts']:
        raise ValueError('Expected original pre-handover Neon backup')
    digest = sample_digest(baseline['samples'])
    print(json.dumps({'phase': 'source_verified', 'registry_ids': 15, 'boundary_log_rows': 9,
                      'batch_sha256': snapshot['source_sha256'], 'apply': args.apply}), flush=True)
    if not args.apply:
        return
    store = PostgresStore(neon_url())
    store.check_schema()
    args.out.mkdir(parents=True, exist_ok=False)
    # Lock the complete before/after snapshot and fail if backup output fails.
    with store.transaction():
        before = backup(store)
        with (args.out / 'before.private-backup.json').open('x', encoding='utf-8') as stream:
            json.dump(before, stream, ensure_ascii=False, allow_nan=False)
        outcome = apply_batch(store, snapshot, digest)
        after = backup(store)
        assert after['samples'] == baseline['samples']
        assert after['documents'] == snapshot['documents'] and after['attempts'] == snapshot['attempts']
        with (args.out / 'after.private-backup.json').open('x', encoding='utf-8') as stream:
            json.dump(after, stream, ensure_ascii=False, allow_nan=False)
        summary = store.summary()
    assert apply_batch(store, snapshot, digest) == 'already_imported'
    os.environ.update(DATABASE_URL=neon_url(), KEYGUARD_STORAGE='postgres',
                      KEYGUARD_ADMIN_KEY='handover-export-check',
                      KEYGUARD_DATA_DIR=str(args.out / 'unused-file-backend'))
    spec = importlib.util.spec_from_file_location('handover_web', ROOT / 'app.py')
    web = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(web)
    response = web.app.test_client().get('/admin/export', headers={'X-Admin-Key': 'handover-export-check'})
    assert response.status_code == 200
    import csv
    with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
        assert json.loads(archive.read('participants.json')) == snapshot['documents']['participants.json']
        assert list(csv.DictReader(io.StringIO(archive.read('attempts.csv').decode('utf-8-sig')))) == snapshot['attempts']
        assert sum(len(archive.read(n).splitlines()) for n in archive.namelist() if n.endswith('.jsonl')) == 601
    report = {
        'date': '2026-11-14', 'project_id': 'bitter-resonance-81924970',
        'source_file_sha256': FILE_HASHES, 'batch_sha256': snapshot['source_sha256'],
        'import_result': outcome, 'summary': summary,
        'historical_601_samples_unchanged': True, 'boundary_log_rows': 9,
        'verify_rows': 4, 'otp_rows': 5, 'registry_ids': 15,
        'registry_timestamps_preserved_without_repair': True,
        'idempotent_reimport_verified': True, 'http_export_values_equal': True,
        'before_after_private_backups_saved': True,
        'not_merged_into_historical_live_33': True,
        'accounts_profiles_recovered': False, 'render_changed': False,
        'provenance_limitations': [
            'Received CSV matches new GitHub boundary-test CSV by fields; no independent server-original proof',
            'No old accounts/profiles recovered; no claim received files are complete current runtime snapshot',
            'Imported attempt rows remain the received values; source batch is tracked by hash and this manifest',
            'Registry P11/P12 timestamp formatting is preserved, not repaired'],
    }
    (args.out / 'validation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'phase': 'handover_import_verified', 'summary': summary,
                      'samples_unchanged': True, 'http_export_equal': True}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Handover import stopped (' + type(error).__name__ + '); credentials withheld', file=sys.stderr)
        raise SystemExit(1)
