"""Independent standard-library reconciliation of USN decisions and summaries."""
import argparse
from collections import Counter,defaultdict
import csv
from datetime import datetime
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];P='results/usn_transfer_20261124_'
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--saved-only',action='store_true');args=parser.parse_args()
    def read(s):return json.loads((ROOT/(P+s)).read_text(encoding='utf-8'))
    f,r,s=map(read,('freeze.json','results.json','started.json'));checks=0;skipped=[]
    def require(value):
        nonlocal checks
        if not value:raise AssertionError('Audit item '+str(checks+1))
        checks+=1
    digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    require(digest(ROOT/(P+'freeze.json'))==r['freeze_sha256']==s['freeze_sha256'])
    require(datetime.fromisoformat(f['frozen_at_utc'])<datetime.fromisoformat(s['started_at_utc'])<datetime.fromisoformat(r['completed_at_utc']))
    verify={**f['code_sha256'],f['protocol']:f['protocol_sha256'],
            'results/usn_source_manifest_20261124.json':f['source_manifest_sha256'],
            'results/usn_schema_audit_20261124.json':f['schema_audit_sha256'],P+'synthetic_tests.json':f['test_report_sha256']}
    if args.saved_only:skipped=list(f['raw_sha256'])+list(f['protected_sha256'])
    else:verify.update(f['raw_sha256']);verify.update(f['protected_sha256'])
    for name,h in verify.items():require(digest(ROOT/name)==h)
    with (ROOT/(P+'accounts.csv')).open(encoding='utf-8',newline='') as stream:accounts=list(csv.DictReader(stream))
    with (ROOT/(P+'decisions.csv')).open(encoding='utf-8',newline='') as stream:decisions=list(csv.DictReader(stream))
    require(len(accounts)==30 and len(decisions)==15610)
    counter=Counter();seen=set();genuine_source=set();attack_source=set()
    for row in decisions:
        require(row['accepted'] in ('True','False'))
        accepted=row['accepted']=='True'
        require((float(row['z'])<=r['threshold'])==accepted)
        key=(row['phrase'],row['target'],row['role'],row['source_line'])
        require(key not in seen);seen.add(key)
        counter[(row['phrase'],row['target'],row['role'],'trials')]+=1
        counter[(row['phrase'],row['target'],row['role'],'errors')]+=int(accepted if row['role']=='attack' else not accepted)
        if row['role']=='genuine':
            require(int(row['source_line'])>=22);genuine_source.add((row['phrase'],row['target'],row['source_line']))
        else:
            require(bool(row['attack_subject']));attack_source.add((row['phrase'],row['source_line']))
    require(len(genuine_source)==5400 and len(attack_source)==2042)
    for row in accounts:
        for role,num,den in [('genuine','genuine_rejected','genuine_trials'),('attack','impostor_accepted','impostor_trials')]:
            require(int(row[num])==counter[(row['phrase'],row['participant_id'],role,'errors')])
            require(int(row[den])==counter[(row['phrase'],row['participant_id'],role,'trials')])
        require(int(row['enrollment_samples'])==20)
    for name,subset in [('overall',accounts)]+[(p,[a for a in accounts if a['phrase']==p]) for p in r['by_phrase']]:
        summary=r['overall'] if name=='overall' else r['by_phrase'][name]
        for metric,num,den in [('far','impostor_accepted','impostor_trials'),('frr','genuine_rejected','genuine_trials')]:
            n=sum(int(a[num]) for a in subset);d=sum(int(a[den]) for a in subset)
            require(summary[num]==n and summary[den]==d)
            require(abs(summary['pooled_'+metric]-float(Fraction(n,d)))<1e-12)
            macro=sum((Fraction(int(a[num]),int(a[den])) for a in subset),Fraction())/len(subset)
            require(abs(summary['macro_'+metric]-float(macro))<1e-12)
        require(summary['accounts_far_above_5pct']==sum(int(a['impostor_accepted'])*20>int(a['impostor_trials']) for a in subset))
    require(r['source_specific_tuning'] is False and r['multi_day_validation'] is False and r['candidate_selection_tested'] is False)
    record={'status':'passed','independent_checks':checks,'decisions_checked':len(decisions),'profiles':len(accounts),
            'unique_attack_rows':len(attack_source),'genuine_evaluation_rows':len(genuine_source),
            'raw_and_historical_archives_checked':not args.saved_only,'archives_not_checked':skipped,
            'scope':'Recomputed every accept decision and account/phrase aggregate from saved scores using standard library; no model rerun'}
    (ROOT/(P+('audit_saved.json' if args.saved_only else 'audit.json'))).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k!='archives_not_checked'}))

if __name__=='__main__':main()
