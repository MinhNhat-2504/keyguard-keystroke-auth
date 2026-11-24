import pytest
from keyguard.residual_score_diagnostic import rank_auc,summarize_saved_scores

@pytest.mark.parametrize('g,a,expected',[([0,1],[2,3],1),([2,3],[0,1],0),([1,1],[1,1],.5),([0,1],[1,2],.875)])
def test_auc_direction_and_ties(g,a,expected):
    result=rank_auc(g,a)
    assert result['auc']==expected

def test_positive_affine_transform_preserves_auc():
    g=[-3,0,1,1,5];a=[-2,1,2,8]
    assert rank_auc(g,a)['auc']==rank_auc([7*x+13 for x in g],[7*x+13 for x in a])['auc']

@pytest.mark.parametrize('g,a',[([], [1]),([0],[]),([float('nan')],[1]),([0],[float('inf')])])
def test_invalid_scores_fail(g,a):
    with pytest.raises(ValueError):rank_auc(g,a)

def fixture():
    rows=[{'phrase':'p','target':'t','role':role,'source_line':str(i+2),'attack_subject':'source1',
           'z':str(z),'accepted':str(z<=0)} for i,(role,z) in enumerate([('genuine',-1),('genuine',1),('attack',-2),('attack',2)])]
    prior={('p','t'):{'oof_scores':[1.]*20,'cv_center':1.,'cv_scale':1.}}
    return rows,prior

def test_all_profiles_retained_and_guard_affects_routes_not_auc():
    rows,prior=fixture()
    a=summarize_saved_scores(rows,{('p','t'):False},0,prior)
    b=summarize_saved_scores(rows,{('p','t'):True},0,prior)
    assert a['remaining_attack_behavioral_passes']==1 and b['remaining_attack_behavioral_passes']==0
    assert a['accounts'][0]['auc']==b['accounts'][0]['auc']==.5
    assert a['decisions_count']==b['decisions_count']==4

def test_duplicate_decision_fails():
    rows,prior=fixture();rows.append(dict(rows[0]))
    with pytest.raises(ValueError):summarize_saved_scores(rows,{('p','t'):False},0,prior)

def test_saved_flag_mismatch_fails():
    rows,prior=fixture();rows[0]['accepted']='False'
    with pytest.raises(ValueError):summarize_saved_scores(rows,{('p','t'):False},0,prior)
