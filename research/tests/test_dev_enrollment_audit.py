import csv
import numpy as np
import pytest
from keyguard.dev_enrollment_audit import read_dev_enrollment

def write(path,kind='CMU',extra=(),mutate=None):
    count=31 if kind=='CMU' else 47
    header=['subject','sessionIndex','rep'] if kind=='CMU' else ['participant','session','repetition']
    features=[f'f{i}' for i in range(count)]
    if kind!='CMU':features[-1]='total time'
    rows=[['dev','1',str(i)]+[str(i)]*count for i in range(25,0,-1)]
    # Values not used for enrollment must never be parsed as timing.
    for row in rows:
        if int(row[2])>20:row[3:] = ['not-a-timing']*count
    rows += [list(r) for r in extra]
    if mutate:mutate(rows)
    with path.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.writer(stream);writer.writerow(header+features);writer.writerows(rows)

@pytest.mark.parametrize('kind',['CMU','KeyRecs'])
def test_only_first_twenty_dev_session_one_are_parsed(tmp_path,kind):
    path=tmp_path/'source.csv'
    write(path,kind,extra=[['test','1','1','poison'],['dev','2','1','poison']])
    values,meta=read_dev_enrollment(path,kind,['dev'])
    assert np.array_equal(values['dev'][:,0],np.arange(1,21))
    assert values['dev'].shape==(20,31 if kind=='CMU' else 47)
    assert meta['enrollment_rows_parsed']==20 and meta['test_or_session2_rows_scored']==0

def test_duplicate_dev_repetition_fails(tmp_path):
    path=tmp_path/'x.csv';write(path,extra=[['dev','1','1']+['0']*31])
    with pytest.raises(ValueError):read_dev_enrollment(path,'CMU',['dev'])

def test_too_few_rows_fails(tmp_path):
    path=tmp_path/'x.csv';write(path,mutate=lambda rows:rows.__delitem__(slice(0,10)))
    with pytest.raises(ValueError):read_dev_enrollment(path,'CMU',['dev'])

@pytest.mark.parametrize('bad',['nan','inf','bad'])
def test_invalid_selected_timing_fails(tmp_path,bad):
    path=tmp_path/'x.csv'
    write(path,mutate=lambda rows:rows[-1].__setitem__(3,bad))
    with pytest.raises(ValueError):read_dev_enrollment(path,'CMU',['dev'])

def test_wrong_source_schema_fails(tmp_path):
    path=tmp_path/'x.csv';write(path)
    with pytest.raises(ValueError):read_dev_enrollment(path,'KeyRecs',['dev'])

def test_duplicate_requested_identity_fails(tmp_path):
    path=tmp_path/'x.csv';write(path)
    with pytest.raises(ValueError):read_dev_enrollment(path,'CMU',['dev','dev'])
