from fractions import Fraction as F
import unittest
from scripts.account_benefit_summary import analyze_accounts, nearest_rank


def record(pid, fa=5, gr=5, it=10, gt=10):
    return dict(participant_id=pid, impostor_accepted=fa, genuine_rejected=gr,
                impostor_trials=it, genuine_trials=gt)


class BenefitTests(unittest.TestCase):
    def test_all_nine_sign_cells_and_complete_account_output(self):
        base, candidate = [], []
        for i, (df, dr) in enumerate((f, r) for f in [-1, 0, 1] for r in [-1, 0, 1]):
            base.append(record(str(i)))
            candidate.append(record(str(i), 5 + df, 5 + dr))
        result = analyze_accounts(base, candidate)
        self.assertEqual(len(result['accounts']), 9)
        self.assertTrue(all(v == 1 for row in result['sign_grid_far_rows_frr_columns'].values() for v in row.values()))
        self.assertEqual(result['guarded_frr_benefit_count'], 2)
        self.assertEqual(result['any_error_increased_count'], 5)
        self.assertFalse(result['primary_met'])

    def test_half_is_not_majority_even_if_global_passes(self):
        base = [record('a'), record('b')]
        result = analyze_accounts(base, [record('a', gr=4), record('b')])
        self.assertTrue(result['primary_met'])
        self.assertFalse(result['broad_benefit_met'])
        self.assertTrue(analyze_accounts(base, [record('a', gr=4), record('b', gr=4)])['broad_benefit_met'])

    def test_majority_benefit_does_not_override_far_harm(self):
        base = [record(str(i)) for i in range(3)]
        result = analyze_accounts(base, [record('0', gr=4), record('1', gr=4), record('2', fa=6)])
        self.assertEqual(result['guarded_frr_benefit_count'], 2)
        self.assertFalse(result['primary_met'])
        self.assertFalse(result['broad_benefit_met'])

    def test_macro_is_not_pooled_with_unequal_denominators(self):
        b = [record('a', gr=2, gt=4), record('b', gr=8, gt=20)]
        c = [record('a', gr=1, gt=4), record('b', gr=6, gt=20)]
        result = analyze_accounts(b, c)
        self.assertEqual(result['delta_macro']['frr'], -F(7, 40))
        self.assertEqual(result['pooled']['candidate']['frr'] - result['pooled']['baseline']['frr'], -F(1, 8))

    def test_nearest_rank_even_odd_and_bounds(self):
        self.assertEqual(nearest_rank([4, 3, 2, 1], 1, 2), 2)
        self.assertEqual(nearest_rank([3, 2, 1], 1, 2), 2)
        self.assertEqual(nearest_rank([3, 2, 1], 1, 1), 3)
        with self.assertRaises(ValueError): nearest_rank([], 1, 2)

    def test_input_rejection(self):
        b = [record('a')]
        for c in ([], [record('b')], [record('a'), record('a')], [record('a', it=11)],
                  [record('a', fa=True)], [record('a', fa=11)], [record('a', gt=0)]):
            with self.assertRaises(ValueError): analyze_accounts(b, c)


if __name__ == '__main__':
    unittest.main()
