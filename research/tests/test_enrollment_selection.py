import copy
import numpy as np
import pytest
from keyguard import enrollment_selection as e


def test_fixed_budget_and_constant_ties():
    x=np.ones((20,3))
    for arm in e.ARMS:
        s=e.select(x,arm)
        assert len(set(s))==10 and np.all(np.diff(s)>0)
    assert e.select(x,'cover10').tolist()==list(range(10))
    assert e.select(x,'last10').tolist()==list(range(10,20))


def test_diverse_representatives_and_input_unchanged():
    x=np.arange(20.)[:,None];old=x.copy()
    chosen=e.select(x,'cover10')
    assert np.array_equal(x,old) and np.array_equal(chosen,e.select(x,'cover10'))
    assert 0 in chosen and 19 in chosen
    assert e.distances(x)[:,chosen].min(axis=1).max() < e.distances(x)[:,:10].min(axis=1).max()


@pytest.mark.parametrize('x',[np.ones((9,2)),np.array([[np.nan]*2]*20),np.ones(20),np.empty((20,0))])
def test_reject_bad_pool(x):
    with pytest.raises(ValueError):e.profile(x,'cover10')


def test_selection_inside_each_cv_training_fold(monkeypatch):
    calls=[];original=e.select
    def inspect(x,arm):
        calls.append(x[:,0].astype(int).tolist())
        return original(x,arm)
    monkeypatch.setattr(e,'select',inspect)
    x=np.column_stack([np.arange(20.),np.arange(20.)**2])
    state=e.profile(x,'cover10')
    for held,seen in zip(np.array_split(np.arange(20),5),calls[:5]):
        assert len(seen)==16 and not set(held)&set(seen)
    assert calls[-1]==list(range(20)) and len(state['selected'])==10


def fixture_data():
    rng=np.random.default_rng(14)
    return {str(i):{'pool':rng.normal(i,.2,(20,3)), 'future':rng.normal(i,.3,(12,3))} for i in range(6)}


def test_future_and_evaluation_identity_do_not_change_threshold_or_selection():
    data=fixture_data();a=e.run_dataset(data,['0','1','2','3'],['4','5'])
    changed=copy.deepcopy(data);changed['4']['future'][:]=1e6
    b=e.run_dataset(changed,['0','1','2','3'],['4','5'])
    for arm in e.ARMS:
        assert a['arms'][arm]['threshold']==b['arms'][arm]['threshold']
        assert [x['selected_positions_1based'] for x in a['arms'][arm]['accounts']]==[x['selected_positions_1based'] for x in b['arms'][arm]['accounts']]
        assert all(x['genuine_trials']==12 and x['impostor_trials']==10 for x in a['arms'][arm]['accounts'])


def test_partition_overlap_rejected():
    with pytest.raises(ValueError):e.run_dataset(fixture_data(),['0','1','2','3'],['3','4','5'])


def test_exact_gate_rejects_far_tradeoff_and_half_benefit():
    base=[{'participant_id':str(i),'genuine_trials':10,'impostor_trials':20,'genuine_rejected':5,'impostor_accepted':1} for i in range(2)]
    candidate=copy.deepcopy(base);candidate[0]['genuine_rejected']=4
    c=e.compare(base,candidate)
    assert c['primary_met'] and not c['majority_benefit_met'] and not c['continuation_gate_met']
    candidate[1]['genuine_rejected']=4;candidate[0]['impostor_accepted']=2
    assert not e.compare(base,candidate)['primary_met']


def test_pairing_and_denominator_mismatch_rejected():
    a=[{'participant_id':'a','genuine_trials':10,'impostor_trials':10,'genuine_rejected':2,'impostor_accepted':1}]
    b=copy.deepcopy(a);b[0]['genuine_trials']=11
    with pytest.raises(ValueError):e.compare(a,b)


def test_split_is_stable_and_subject_disjoint():
    a,b=e.split_existing_dev([str(i) for i in range(36)])
    assert len(a)==24 and len(b)==12 and not set(a)&set(b)
    assert (a,b)==e.split_existing_dev(list(reversed([str(i) for i in range(36)])))


def test_threshold_keeps_tied_group_intact():
    t=e.threshold_at_far(np.ones(20),.05)
    assert np.count_nonzero(np.ones(20)<=t)==0
