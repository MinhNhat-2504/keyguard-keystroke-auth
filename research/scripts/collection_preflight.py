"""Read-only JSONL preflight for future collection; never repairs or drops rows."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path

EXPECTED = list('.tie5Roanl') + ['Enter']
MODIFIERS = {'shift','control','alt','meta','capslock','altgraph'}
TYPES = {'down':'down','keydown':'down','up':'up','keyup':'up'}


def event_issues(events):
    if not isinstance(events, list) or not events:
        return ['events_missing_or_invalid']
    if len(events) > 256:
        return ['events_too_many']
    issues, active, typed = set(), {}, []
    previous = -float('inf')
    for e in events:
        if not isinstance(e, dict):
            issues.add('event_not_object'); continue
        key, t, kind = e.get('key'), e.get('t'), e.get('type')
        if not isinstance(key,str) or not key or not isinstance(kind,str) or kind not in TYPES:
            issues.add('event_key_or_type_invalid'); continue
        if isinstance(t,bool) or not isinstance(t,(int,float)) or not math.isfinite(t) or t < 0:
            issues.add('event_time_invalid'); continue
        if t < previous: issues.add('event_order_not_monotonic')
        previous = t
        norm = 'enter' if key.lower() in {'enter','return'} else key.lower()
        code = e.get('code')
        if code is not None and (not isinstance(code,str) or not code.strip()):
            issues.add('event_code_invalid'); continue
        identity = ('code',code) if code is not None else ('key',norm)
        if TYPES[kind] == 'down':
            if identity in active:
                issues.add('repeated_down_without_up'); continue
            active[identity] = (t,norm)
            if norm not in MODIFIERS:
                typed.append('Enter' if norm == 'enter' else key)
        else:
            start = active.pop(identity,None)
            if start is None:
                issues.add('up_without_down')
            else:
                if t < start[0]: issues.add('negative_hold')
                if norm != start[1]: issues.add('key_changed_on_same_code')
    if active: issues.add('down_without_up')
    if typed != EXPECTED: issues.add('phrase_or_case_mismatch')
    return sorted(issues)


def record_issues(record):
    if not isinstance(record,dict): return ['record_not_object'], None
    issues = []
    pid = record.get('participant_id')
    valid_id = isinstance(pid,str) and bool(pid.strip()) and pid == pid.strip()
    if not valid_id: issues.append('participant_id_invalid')
    valid_numbers = all(type(record.get(k)) is int and record[k] > 0 for k in ('session','rep'))
    if not valid_numbers: issues.append('session_or_rep_invalid')
    timestamp = record.get('collected_at')
    try:
        if not isinstance(timestamp,str): raise ValueError()
        dt = datetime.fromisoformat(timestamp.replace('Z','+00:00'))
        if dt.tzinfo is None or dt.utcoffset() is None: raise ValueError()
    except (ValueError,TypeError,OverflowError): issues.append('collected_at_missing_or_timezone_invalid')
    # A pseudonymous device code, not a UA string or a verified hardware identity.
    device = record.get('device_id')
    if not isinstance(device,str) or not device.strip(): issues.append('device_id_missing')
    issues.extend(event_issues(record.get('events')))
    key = (pid,record['session'],record['rep']) if valid_id and valid_numbers else None
    return issues,key


def audit(paths):
    rows, locations, sources = [], defaultdict(list), []
    resolved = [Path(p).resolve() for p in paths]
    if len(set(resolved)) != len(resolved): raise ValueError('Input file listed twice')
    if not resolved: raise ValueError('No input files')
    for file_index,path in enumerate(resolved,1):
        data = path.read_bytes()
        sources.append({'input':file_index,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
        for lineno,line in enumerate(data.decode('utf-8-sig').splitlines(),1):
            if not line.strip(): continue
            try:
                def unique_object(pairs):
                    obj={}
                    for k,v in pairs:
                        if k in obj: raise ValueError('Duplicate JSON field')
                        obj[k]=v
                    return obj
                record=json.loads(line,object_pairs_hook=unique_object,
                                  parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
                issues,key=record_issues(record)
            except (ValueError,RecursionError):
                issues,key=['json_invalid'],None
            row={'input':file_index,'line':lineno,'issues':issues}
            rows.append(row)
            # Register valid keys even when the record has other defects.
            if key is not None: locations[key].append(len(rows)-1)
    groups=0
    for indices in locations.values():
        if len(indices)>1:
            groups+=1
            for i in indices: rows[i]['issues'].append('duplicate_participant_session_rep')
    counts=Counter(code for row in rows for code in row['issues'])
    return {'status':'needs_review' if not rows or any(r['issues'] for r in rows) else 'passed',
            'empty_input':not rows,
            'scope':'Future-collection preflight, not consent/identity/server-time proof or a legacy exclusion rule',
            'input_sha256':sources,'records':len(rows),'records_needing_review':sum(bool(r['issues']) for r in rows),
            'duplicate_key_groups':groups,'issue_counts':dict(sorted(counts.items())),
            'review_rows':[r for r in rows if r['issues']],
            'input_modified':False,'rows_repaired_or_removed':0,'raw_events_or_participant_ids_in_report':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs',nargs='+',type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    if args.out.resolve() in [p.resolve() for p in args.inputs]: parser.error('Output cannot overwrite input')
    report=audit(args.inputs)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','records','records_needing_review','issue_counts','input_modified')}))
    return 0 if report['status']=='passed' else 2


if __name__=='__main__': raise SystemExit(main())
