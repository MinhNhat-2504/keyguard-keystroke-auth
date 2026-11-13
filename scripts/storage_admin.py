"""Explicit PostgreSQL initialization/import and private full backup; never auto-migrate."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pg_storage import PostgresStore


def legacy_snapshot(source):
    source = Path(source).resolve()
    if not source.is_dir():
        raise ValueError('Legacy source directory does not exist')
    documents, samples, attempts, hashes = {}, [], [], {}
    for name in ('participants.json', 'accounts.json', 'challenges.json'):
        path = source / name
        if path.exists():
            raw = path.read_bytes()
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError('Invalid legacy registry')
            documents[name] = value
            hashes[name] = hashlib.sha256(raw).hexdigest()
    for path in sorted((source / 'profiles').glob('*.json')):
        if not re.fullmatch(r'[0-9a-f]{32}', path.stem):
            raise ValueError('Invalid profile filename')
        raw = path.read_bytes()
        value = json.loads(raw)
        if not isinstance(value, dict) or not isinstance(value.get('samples'), list):
            raise ValueError('Invalid profile payload')
        documents['profiles/' + path.name] = value
        hashes['profiles/' + path.name] = hashlib.sha256(raw).hexdigest()
    for path in sorted((source / 'collected').glob('*.jsonl')):
        if not re.fullmatch(r'P\d{2,4}', path.stem):
            raise ValueError('Invalid participant filename')
        raw = path.read_bytes()
        hashes['collected/' + path.name] = hashlib.sha256(raw).hexdigest()
        for line in raw.decode('utf-8-sig').splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get('participant_id') != path.stem or not isinstance(row.get('events'), list):
                raise ValueError('Invalid/mismatched collected row')
            samples.append(row)  # Preserve ambiguous historical reps, never silently repair.
    path = source / 'attempts.csv'
    if path.exists():
        hashes['attempts.csv'] = hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open(encoding='utf-8-sig', newline='') as stream:
            attempts = list(csv.DictReader(stream))
        if any(row.get('event') not in ('verify', 'otp') for row in attempts):
            raise ValueError('Invalid attempt event')
    for entry in documents.get('accounts.json', {}).values():
        if not isinstance(entry, dict) or 'profiles/' + str(entry.get('id')) + '.json' not in documents:
            raise ValueError('Account refers to missing profile; cannot import a partial account backup')
    source_hash = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    return {'documents': documents, 'samples': samples, 'attempts': attempts,
            'source_sha256': source_hash, 'source_file_sha256': hashes}


def import_snapshot(store, snapshot):
    with store.transaction() as connection:
        seen = connection.execute('SELECT 1 FROM kg_imports WHERE source_sha256=%s', (snapshot['source_sha256'],)).fetchone()
        if seen:
            return 'already_imported'
        if any(store.summary().values()):
            raise RuntimeError('Target is not empty; refuse to merge or overwrite existing runtime data')
        for name, value in snapshot['documents'].items():
            store.put(name, value)
        for row in snapshot['samples']:
            store.append_sample(row['participant_id'], row)
        for row in snapshot['attempts']:
            store.append_attempt(row)
        connection.execute('INSERT INTO kg_imports(source_sha256) VALUES (%s)', (snapshot['source_sha256'],))
    return 'imported'


def backup(store):
    with store.transaction() as connection:
        documents = {row[0]: row[1] for row in connection.execute('SELECT name,payload FROM kg_documents ORDER BY name')}
        samples = [r[0] for r in connection.execute('SELECT payload FROM kg_samples ORDER BY id')]
        return {'format': 'keyguard-private-backup-v1', 'documents': documents,
                'samples': samples, 'attempts': store.attempts()}


def restore_backup(store, payload):
    if payload.get('format') != 'keyguard-private-backup-v1':
        raise ValueError('Unsupported backup format')
    # Validate references on restore, not arbitrary external object keys.
    for name, value in payload['documents'].items():
        if name not in ('accounts.json', 'participants.json', 'challenges.json') and not re.fullmatch(r'profiles/[0-9a-f]{32}\.json', name):
            raise ValueError('Invalid backup document key')
        if not isinstance(value, dict):
            raise ValueError('Invalid backup document')
    for entry in payload['documents'].get('accounts.json', {}).values():
        if 'profiles/' + str(entry.get('id')) + '.json' not in payload['documents']:
            raise ValueError('Backup account has no profile')
    raw = json.dumps(payload, sort_keys=True, allow_nan=False).encode()
    return import_snapshot(store, {**payload, 'source_sha256': hashlib.sha256(raw).hexdigest()})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('init', 'status', 'import-files', 'backup', 'restore'))
    parser.add_argument('--source', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--apply', action='store_true', help='Required for data import/restore, dry-run otherwise')
    args = parser.parse_args(argv)
    if args.command == 'import-files':
        if args.source is None:
            parser.error('--source directory required')
        snapshot = legacy_snapshot(args.source)
        print(json.dumps({'documents': len(snapshot['documents']), 'samples': len(snapshot['samples']),
                          'attempts': len(snapshot['attempts']), 'source_sha256': snapshot['source_sha256'],
                          'mode': 'apply' if args.apply else 'dry_run_no_database_write'}))
        if not args.apply:
            return
    if args.command == 'restore':
        if args.source is None:
            parser.error('--source backup file required')
        payload = json.loads(args.source.read_text(encoding='utf-8'))
        if not args.apply:
            print('Dry-run: backup parsed, not imported; --apply validates references and writes only to empty target')
            return
    store = PostgresStore(os.environ.get('DATABASE_URL'))
    if args.command == 'init':
        store.initialize()
        print('PostgreSQL schema initialized; no legacy data imported')
        return
    store.check_schema()
    if args.command == 'status':
        print(json.dumps(store.summary()))
    elif args.command == 'import-files':
        print(import_snapshot(store, snapshot))
    elif args.command == 'restore':
        print(restore_backup(store, payload))
    elif args.command == 'backup':
        if args.out is None:
            parser.error('--out required for private backup; never print profiles to console')
        with args.out.open('x', encoding='utf-8') as stream:
            json.dump(backup(store), stream, ensure_ascii=False, allow_nan=False)
        print('Private backup written; includes accounts/profiles/challenges. Keep out of GitHub.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Connection exceptions can contain provider hostnames; never print DATABASE_URL.
        print(f'Storage operation failed ({type(error).__name__}); no file fallback. Check private local logs/config.', file=sys.stderr)
        raise SystemExit(1)
