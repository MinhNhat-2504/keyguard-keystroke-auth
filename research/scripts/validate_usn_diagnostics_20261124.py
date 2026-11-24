"""Reconcile retrospective summaries without NumPy or model imports."""
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[1]
def main():
    sensitivity=json.loads((ROOT/'results/usn_sensitivity_20261124.json').read_text(encoding='utf-8'))
    diagnostic=json.loads((ROOT/'results/usn_oof_diagnostic_20261124.json').read_text(encoding='utf-8'))
    with (ROOT/'results/usn_transfer_20261124_accounts.csv').open(encoding='utf-8',newline='') as s:accounts=list(csv.DictReader(s))
    checks=0
    def require(ok):
        nonlocal checks
        assert ok,'Independent diagnostic check '+str(checks+1)
        checks+=1
    for artifact in (sensitivity,diagnostic):
        for n,h in artifact['source_sha256'].items():require(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h)
    def compare(summary,rows):
        require(summary['profiles']==len(rows))
        for metric,num,den in [('far','impostor_accepted','impostor_trials'),('frr','genuine_rejected','genuine_trials')]:
            n=sum(int(r[num]) for r in rows);d=sum(int(r[den]) for r in rows)
            require(n==summary[num] and d==summary[den])
            require(abs(float(Fraction(n,d))-summary['pooled_'+metric])<1e-12)
            m=sum((Fraction(int(r[num]),int(r[den])) for r in rows),Fraction())/len(rows)
            require(abs(float(m)-summary['macro_'+metric])<1e-12)
    results=sensitivity['results'];compare(results['overall'],accounts)
    for pid,s in results['by_person'].items():compare(s,[r for r in accounts if r['participant_id']==pid])
    for pid,s in results['leave_one_person'].items():compare(s,[r for r in accounts if r['participant_id']!=pid])
    for phrase,s in results['leave_one_phrase'].items():compare(s,[r for r in accounts if r['phrase']!=phrase])
    bounds=results['excluded_attack_decision_bounds']
    require(bounds['additional_unknown_decisions']==135 and bounds['raw_row_scenario_trials']==10345)
    require(bounds['lower']==float(Fraction(1394,10345)) and bounds['upper']==float(Fraction(1529,10345)))
    require(len(diagnostic['profiles'])==30 and diagnostic['all_30_saved_cv_summaries_reproduced'])
    for d in diagnostic['profiles']:
        a=next(a for a in accounts if a['phrase']==d['phrase'] and a['participant_id']==d['participant_id'])
        require(len(d['oof_scores'])==20)
        require(abs(statistics.mean(d['oof_scores'])-d['cv_center'])<=max(1e-10,abs(d['cv_center'])*1e-12))
        require(abs(max(statistics.pstdev(d['oof_scores']),1e-6)-d['cv_scale'])<=max(1e-10,abs(d['cv_scale'])*1e-12))
        require(abs(d['cv_center']-float(a['cv_center']))<=max(1e-10,abs(d['cv_center'])*1e-12))
        require(abs(d['cv_scale']-float(a['cv_scale']))<=max(1e-10,abs(d['cv_scale'])*1e-12))
        require(abs(d['equivalent_raw_score_limit']-(d['cv_center']+.2720094565367825*d['cv_scale']))<1e-9)
        if d['phrase']=='Ob-dollar-erv3r' and d['participant_id'] in ('participant1','participant2','participant3'):
            require(d['largest_oof']['largest_contribution']==1000000.0)
            require(d['largest_oof']['feature_name']=="down to down '#CTRL#' => '#ALT#'")
            require(d['full_enrollment_floored_feature_indices']==[])
            require(any(f['max_held_absolute_deviation']==.001 and f['max_score_contribution']==1000000.0 for f in d['floored_training_features']))
    record={'status':'passed','independent_checks':checks,'profile_cv_summaries':30,'person_omissions':5,'phrase_omissions':6,'scope':'Saved OOF statistics and count reconciliation; no model rerun or claim of a correction'}
    (ROOT/'results/usn_diagnostics_validation_20261124.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))

if __name__=='__main__':main()
