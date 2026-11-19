import unittest
import numpy as np
from scipy.stats import bootstrap
from scripts.account_uncertainty import paired_rates, summarize


class UncertaintyTests(unittest.TestCase):
    def test_independent_scipy_reference(self):
        data = np.array([[.01,.2,.02,.1],[.05,.8,.06,.9],[.03,.5,.01,.4],[.12,.4,.1,.2]])
        actual = summarize(data, 1000, 7)
        def statistic(a,b,c,d,axis=-1):
            return np.array([np.mean(a,axis), np.mean(b,axis), np.mean(c,axis), np.mean(d,axis),
                             np.mean(c-a,axis), np.mean(d-b,axis)])*100
        ref = bootstrap(tuple(data.T), statistic, paired=True, vectorized=True, n_resamples=1000,
                        method='percentile', rng=np.random.default_rng(7))
        np.testing.assert_allclose([x['lower_pp'] for x in actual.values()], ref.confidence_interval.low, atol=1e-12)
        np.testing.assert_allclose([x['upper_pp'] for x in actual.values()], ref.confidence_interval.high, atol=1e-12)

    def test_pairing_preserves_zero_differences(self):
        x = np.array([[.0,.2,.0,.2],[.8,.4,.8,.4],[.3,.9,.3,.9]])
        for key in ('delta_far','delta_frr'):
            self.assertEqual(summarize(x, 100, 3)[key], dict(estimate_pp=0., lower_pp=0., upper_pp=0.))

    def test_macro_does_not_weight_by_trials(self):
        rows = [dict(participant_id='a',impostor_accepted=0,impostor_trials=10,genuine_rejected=0,genuine_trials=10),
                dict(participant_id='b',impostor_accepted=100,impostor_trials=100,genuine_rejected=100,genuine_trials=100)]
        self.assertEqual(summarize(paired_rates(rows, rows),100)['control_far']['estimate_pp'],50)
        self.assertEqual(paired_rates(rows, list(reversed(rows))).tolist(), [[0,0,0,0],[1,1,1,1]])

    def test_bad_pairs_counts_and_rates_rejected(self):
        r = dict(participant_id='a',impostor_accepted=0,impostor_trials=10,genuine_rejected=0,genuine_trials=10)
        other = dict(r, participant_id='b')
        for a,b in [([r,r],[r,other]),([r,other],[r]),([r,other],[r,dict(other,genuine_trials=11)]),
                    ([r,dict(other,impostor_accepted=11)],[r,other]),([r,dict(other,genuine_trials=True)],[r,other])]:
            with self.assertRaises(ValueError): paired_rates(a,b)
        with self.assertRaises(ValueError): summarize([[float('nan')]*4]*2)


if __name__ == '__main__': unittest.main()
