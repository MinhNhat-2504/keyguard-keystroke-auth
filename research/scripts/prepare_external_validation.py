"""Audit only; no model scoring. Freeze split/schema/code before first evaluation."""
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding='utf-8')
from keyguard.external_validation import read_keyrecs, fixed_split

FILES = ['keyguard/external_validation.py', 'keyguard/soft_weighting.py', 'keyguard/enrollment_study.py',
         'keyguard/session_adaptation.py', 'keyguard/detectors.py', 'keyguard/evaluation.py',
         'keyguard/model.py', 'keyguard/research.py', 'scripts/run_external_validation.py',
         'docs/EXTERNAL_VALIDATION_PROTOCOL.md']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    raw = ROOT/'data/raw/keyrecs/fixed-text.csv'
    metadata = json.loads((ROOT/'data/raw/keyrecs/metadata.json').read_text(encoding='utf-8'))
    assert metadata['metadata']['license']['id'] == 'cc-by-4.0'
    expected = next(f['checksum'].split(':')[1] for f in metadata['files'] if f['key'] == 'fixed-text.csv')
    assert hashlib.md5(raw.read_bytes()).hexdigest() == expected == 'f3c2ef3a42625f4df7183ea36d4543db'
    data, audit = read_keyrecs(raw)
    dev, test = fixed_split(list(data))
    document = {'schema_version': 1, 'state': 'frozen_before_first_evaluation', 'date': '2026-11-13',
                'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
                'dataset': {'name': 'KeyRecs fixed-text', 'record': 'https://zenodo.org/records/7886743',
                            'article': 'https://doi.org/10.1016/j.dib.2023.109509',
                            'license': 'CC BY 4.0', 'license_url': 'https://creativecommons.org/licenses/by/4.0/',
                            'authors': ['Tiago Dias', 'João Vitorino', 'Eva Maia', 'Orlando Sousa', 'Isabel Praça'],
                            'file': 'data/raw/keyrecs/fixed-text.csv', 'md5': expected, 'sha256': sha(raw)},
                'audit': audit, 'dev_ids': dev, 'test_ids': test, 'seed': 42,
                'schema_clarification_before_scoring': '46 digraph timing columns plus total time; retain all47 timing descriptors. Repeated DU.k.k preserved by position, second named __occ2.',
                'families': {'baseline': ['keep_all__mean_std'],
                             'hard_selected': [f'hard_filter__{c}' for c in ('mean_std','median_mad','median_iqr')],
                             'soft_selected': [f'soft_weight__{c}' for c in ('mean_std','median_mad','median_iqr')],
                             'all_selected': [f'{q}__{c}' for q in ('keep_all','hard_filter','soft_weight')
                                               for c in ('mean_std','median_mad','median_iqr')]},
                'external_dev_use': 'session1 only, enroll20 then remaining genuine; impostors first5+last5 same partition session1',
                'external_test_use': 'session2 only for genuine and first5+last5 impostors of same test partition; enroll20 session1',
                'adaptation': {'methods': ['static','window50','decay20'],
                               'dev_threshold': 'probe session1 immediately after20 enrollment',
                               'test': 'warmup remaining session1 verified genuine, score/update session2; probe at session2 start',
                               'oracle_updates': True, 'half_life':20,'window':50},
                'primary_comparison': 'soft_selected versus baseline, report FAR/FRR and macro per-account EER/AUC, no universal win if any metric worse',
                'no_model_scores_in_audit': True, 'no_public_preregistration_claim': True,
                'code_hashes': {name: sha(ROOT/name) for name in FILES},
                'production_config_sha256': sha(ROOT/'models/model_config.json')}
    path = ROOT/'results/external_validation_freeze.json'
    if path.exists():
        old = json.loads(path.read_text(encoding='utf-8'))
        document['frozen_at_utc'] = old['frozen_at_utc']
        if document != old:
            raise RuntimeError('Frozen protocol already exists and differs; preserve original and document an amendment instead')
    else:
        path.write_text(json.dumps(document, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('FROZEN: schema', audit['feature_count'], 'features;', len(data), 'eligible IDs;', len(dev), 'dev /',len(test),'test; no model scores computed')
    print('Freeze SHA256:', sha(path))


if __name__ == '__main__': main()
