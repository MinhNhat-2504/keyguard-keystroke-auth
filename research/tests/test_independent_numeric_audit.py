"""Adversarial fixtures for the independent arithmetic auditor, no scientific data."""
import copy
import unittest
from scripts.audit_results_independent_20261122 import Audit


class IndependentAuditTests(unittest.TestCase):
    def test_rehashed_or_well_formed_wrong_rate_is_rejected(self):
        with self.assertRaises(AssertionError):
            Audit().walk(dict(genuine_trials=10, genuine_rejected=3,
                              impostor_trials=20, impostor_accepted=2, frr=.2, far=.1), 'fixture')

    def test_macro_is_distinct_from_pooled(self):
        row = dict(genuine_trials=110, genuine_rejected=11, impostor_trials=20,
                   impostor_accepted=2, metric_basis='macro_accounts', frr=.505,
                   far=.1, pooled_frr=.1, pooled_far=.1)
        Audit().walk(row, 'valid_macro_summary')

    def test_account_totals_cannot_hide_changed_denominator(self):
        account = dict(participant_id='fake', genuine_trials=10, genuine_rejected=3,
                       impostor_trials=20, impostor_accepted=2)
        parent = dict(accounts=[account], overall={**account, 'genuine_trials': 11})
        with self.assertRaises(AssertionError):
            Audit().walk(parent, 'fixture')

    def test_overlap_is_rejected(self):
        with self.assertRaises(AssertionError):
            Audit().walk(dict(dev_ids=['fake_a'], test_ids=['fake_a']), 'fixture')

    def test_unequal_account_sizes_use_unweighted_macro(self):
        a = dict(participant_id='fake_a', genuine_trials=10, genuine_rejected=1,
                 impostor_trials=20, impostor_accepted=2)
        b = {**a, 'participant_id': 'fake_b', 'genuine_trials': 100, 'genuine_rejected': 50}
        valid = dict(accounts=[a,b], macro_frr=.3, macro_far=.1)
        Audit().walk(valid, 'fixture')
        invalid = copy.deepcopy(valid);invalid['macro_frr'] = 51/110
        with self.assertRaises(AssertionError):
            Audit().walk(invalid, 'fixture')


if __name__ == '__main__':
    unittest.main()
