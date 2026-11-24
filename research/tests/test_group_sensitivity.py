from copy import deepcopy
import pytest
from keyguard.group_sensitivity import summarize_groups

def fixture():
    return [dict(target=t,phrase=p,genuine_trials=10,attack_trials=20,
                 genuine_additional_verification_before=1,genuine_additional_verification_after=1+(t=='b'),
                 attack_behavioral_before=4,attack_behavioral_after=0 if t=='a' else 4)
            for t in ('a','b') for p in ('x','y')]

def test_pooled_counts_and_paired_cost():
    r=summarize_groups(fixture())['overall']
    assert (r['attack_behavioral_before'],r['attack_behavioral_after'],r['attack_trials'])==(16,8,80)
    assert r['attack_direct_rate_after']==.1 and r['genuine_extra_rate_after']==.15
    assert r['genuine_moved_to_extra']==2 and r['attack_moved_to_extra']==8

def test_every_group_removed_exactly_once_without_refitting():
    r=summarize_groups(fixture())
    assert [x['excluded'] for x in r['leave_one_target_out']]==['a','b']
    assert [x['attack_behavioral_after'] for x in r['leave_one_target_out']]==[8,0]
    assert [x['profiles'] for x in r['leave_one_phrase_out']]==[2,2]

def test_weighted_pooled_rate_not_unweighted_profile_mean():
    rows=fixture();rows[0]['attack_trials']=200
    assert summarize_groups(rows)['overall']['attack_direct_rate_before']==16/260

def test_order_independent_and_inputs_preserved():
    rows=fixture();old=deepcopy(rows)
    assert summarize_groups(rows)==summarize_groups(reversed(rows)) and rows==old

@pytest.mark.parametrize('kind',['duplicate','missing','negative','fraction','too_large','reverse','empty'])
def test_invalid_inputs_rejected(kind):
    rows=fixture()
    if kind=='duplicate':rows.append(dict(rows[0]))
    if kind=='missing':rows.pop()
    if kind=='negative':rows[0]['attack_behavioral_before']=-1
    if kind=='fraction':rows[0]['attack_trials']=20.0
    if kind=='too_large':rows[0]['attack_behavioral_before']=21
    if kind=='reverse':rows[0]['attack_behavioral_after']=5
    if kind=='empty':rows=[]
    with pytest.raises(ValueError):summarize_groups(rows)
