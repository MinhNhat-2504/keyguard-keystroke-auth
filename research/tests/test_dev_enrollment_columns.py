"""Regression for repeated source headers; added during independent validation."""
import csv
import numpy as np
from keyguard.dev_enrollment_audit import read_dev_enrollment

def test_duplicate_feature_names_keep_distinct_column_values(tmp_path):
    path=tmp_path/'keyrecs.csv'
    header=['participant','session','repetition']+['same','same']+[f'f{i}' for i in range(44)]+['total time']
    assert len(header)==50
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(header)
        for i in range(1,21):writer.writerow(['p001','1',str(i)]+[11.,22.]+[float(i)]*45)
    data,meta=read_dev_enrollment(path,'KeyRecs',['p001'])
    assert meta['feature_names'][:2]==['same','same']
    assert np.array_equal(data['p001'][:,0],np.full(20,11.))
    assert np.array_equal(data['p001'][:,1],np.full(20,22.))
