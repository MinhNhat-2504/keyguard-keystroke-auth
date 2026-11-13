"""Check Neon TLS and schema readiness using SELECT only; never print credentials."""
import json
import os
import sys
from urllib.parse import parse_qs, urlparse

import psycopg


def main():
    url = os.environ.get('DATABASE_URL_UNPOOLED') or os.environ.get('DATABASE_URL', '')
    parsed = urlparse(url)
    if not parsed.hostname or not parsed.hostname.endswith('.neon.tech'):
        raise ValueError('Expected Neon database configuration')
    if parse_qs(parsed.query).get('sslmode', [''])[0] not in ('require', 'verify-ca', 'verify-full'):
        raise ValueError('TLS required')
    with psycopg.connect(url, connect_timeout=15) as connection:
        connection.execute('SET TRANSACTION READ ONLY')
        ok = connection.execute('SELECT 1').fetchone()[0] == 1
        # Inspect this client's TLS transport; a proxy may terminate TLS before
        # the backend represented by pg_stat_ssl.
        tls = bool(connection.pgconn.ssl_in_use)
        exists = connection.execute('SELECT to_regclass(%s) IS NOT NULL', ('public.kg_schema',)).fetchone()[0]
        connection.rollback()
    if not ok or not tls:
        raise RuntimeError('Connection or TLS check failed')
    print(json.dumps({'connection_ok': ok, 'tls': tls, 'keyguard_schema_exists': exists,
                      'read_only_check': True, 'tables_created': False, 'data_imported': False}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Neon connection check failed (' + type(error).__name__ + '); credentials withheld', file=sys.stderr)
        raise SystemExit(1)
