"""Load only fixed DEV enrollment values; preserve the original source columns."""
import csv
from pathlib import Path
import numpy as np

def read_dev_enrollment(path, kind, dev_ids):
    allowed=set(dev_ids)
    if not allowed or len(allowed)!=len(dev_ids):raise ValueError('Distinct DEV identities required')
    selected={pid:[] for pid in sorted(allowed)};seen=set()
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.reader(stream);header=next(reader)
        if kind=='CMU':
            if header[:3]!=['subject','sessionIndex','rep'] or len(header)!=34:raise ValueError('CMU schema mismatch')
        elif kind=='KeyRecs':
            if header[:3]!=['participant','session','repetition'] or len(header)!=50 or header[-1]!='total time':raise ValueError('KeyRecs schema mismatch')
        else:raise ValueError('Unknown source')
        for line,fields in enumerate(reader,2):
            if not fields or fields[0] not in allowed:continue
            if len(fields)<3:raise ValueError('DEV metadata missing')
            if fields[1]!='1':continue
            rep=int(fields[2])
            if rep<1 or (fields[0],rep) in seen:raise ValueError('Invalid/duplicate DEV repetition')
            seen.add((fields[0],rep));selected[fields[0]].append((rep,line,fields))
    output={};lines={}
    for pid,records in selected.items():
        records=sorted(records)[:20]
        if len(records)!=20:raise ValueError('Twenty enrollment rows required')
        if any(len(fields)!=len(header) for _,_,fields in records):raise ValueError('Feature count mismatch')
        x=np.asarray([[float(v) for v in fields[3:]] for _,_,fields in records],dtype=float)
        if not np.isfinite(x).all():raise ValueError('Finite DEV enrollment required')
        output[pid]=x;lines[pid]=[line for _,line,_ in records]
    return output,{'feature_names':header[3:],'enrollment_rows_parsed':20*len(output),
                   'enrollment_lines':lines,'test_or_session2_rows_scored':0}
