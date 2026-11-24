"""Strict USN v1 adapter; metadata are not features, no scoring in audit."""
from collections import Counter
import csv
import math
from pathlib import Path
import re

PHRASES=('flying automatic monster','Gigab-exclm-t R3ceiver','gigabit receiver',
         'Ob-dollar-erv3r','observer','repetition learn machine thinker')

def read_file(path, attack):
    path=Path(path)
    with path.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.reader(stream);header=next(reader)
        if attack and header[:2]!=['subject','rep']:raise ValueError('Attack metadata schema')
        timing=header[2:] if attack else header
        if len(timing)<4 or len(timing)%3!=1:raise ValueError('Timing schema length')
        for i,name in enumerate(timing):
            prefix=('hold time ', 'down to down ', 'up to down ')[i%3]
            if not name.startswith(prefix):raise ValueError('Timing column order')
        if timing[-1]!="hold time '#ENTER#'":raise ValueError('Missing terminal Enter')
        rows=[];excluded=[];total=0
        for line,fields in enumerate(reader,2):
            total+=1
            try:
                if len(fields)!=len(header):raise ValueError('column_count')
                if attack:
                    if not all(re.fullmatch(r'[1-9][0-9]*',v) for v in fields[:2]):raise ValueError('metadata')
                    identity,rep=map(int,fields[:2])
                else:identity,rep=None,total
                values=fields[2:] if attack else fields
                if any(not v.strip() for v in values):raise ValueError('blank_timing')
                x=list(map(float,values))
                if not all(math.isfinite(v) for v in x):raise ValueError('nonfinite_timing')
                rows.append({'line':line,'subject':identity,'rep':rep,'x':x})
            except (ValueError,OverflowError) as exc:
                excluded.append({'line':line,'reason':str(exc),'subject':fields[0] if attack and fields else None})
    if attack:
        counts=Counter((r['subject'],r['rep']) for r in rows)
        ambiguous={key for key,n in counts.items() if n>1}
        keep=[]
        for r in rows:
            if (r['subject'],r['rep']) in ambiguous:excluded.append({'line':r['line'],'reason':'ambiguous_duplicate_key','subject':r['subject']})
            else:keep.append(r)
        rows=keep
    audit={'file':path.name,'raw_rows':total,'retained_rows':len(rows),'feature_count':len(timing),
           'excluded':excluded,'has_session_or_timestamp':False,
           'negative_hold_values':sum(v<0 for r in rows for v in r['x'][::3]),
           'max_dd_minus_h_ud_abs':max((abs(r['x'][i+1]-r['x'][i]-r['x'][i+2]) for r in rows for i in range(0,len(timing)-1,3)),default=0),
           'unique_attack_ids':len({r['subject'] for r in rows}) if attack else None}
    return timing,rows,audit

def load_source(folder):
    folder=Path(folder);data={};audit=[]
    for phrase in PHRASES:
        header,attack,report=read_file(folder/f'attack - {phrase}.csv',True);audit.append(report)
        genuine={}
        for person in range(1,6):
            own,rows,report=read_file(folder/f'participant{person} - {phrase}.csv',False)
            if own!=header:raise ValueError('Attack/genuine feature mismatch')
            if len(rows)!=200:raise ValueError('Expected all 200 genuine rows')
            genuine[f'participant{person}']=rows;audit.append(report)
        if len(attack)<100:raise ValueError('Insufficient attack rows')
        data[phrase]={'header':header,'attack':attack,'genuine':genuine}
    return data,{'files':audit,'raw_rows':sum(a['raw_rows'] for a in audit),
                 'retained_rows':sum(a['retained_rows'] for a in audit),'excluded_rows':sum(len(a['excluded']) for a in audit),
                 'model_scoring_performed':False,'scope':'Source/schema audit; row order is not verified chronological order'}
