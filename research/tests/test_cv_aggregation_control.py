"""Synthetic-only tests for shared-detector, fixed-threshold CV aggregation."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from keyguard.matched_adaptation import evaluate_test, validate_data
from keyguard.session_adaptation import fit_history
from keyguard.soft_weighting import WeightedManhattan
from scripts import cv_aggregation_core as core
from scripts import run_cv_aggregation_control as runner


def toy():
    rng = np.random.default_rng(232)
    return {str(i): {1: rng.uniform(.1, .3, (26, 3)),
                     2: rng.uniform(.1, .3, (10 + i, 3))} for i in range(4)}


def account(pid, fa, imp, fr, genuine):
    return {'participant_id': pid, 'impostor_accepted': fa, 'impostor_trials': imp,
            'genuine_rejected': fr, 'genuine_trials': genuine}


class AggregationCoreTest(unittest.TestCase):
    def test_weighted_population_formula_and_equal_weights(self):
        q, w = np.array([1., 2., 8.]), np.array([1., 2., 4.])
        center, scale = core.aggregate(q, w)
        self.assertEqual(center, 37 / 7)
        expected_variance = ((1 - 37 / 7) ** 2 + 2 * (2 - 37 / 7) ** 2 + 4 * (8 - 37 / 7) ** 2) / 7
        self.assertAlmostEqual(scale ** 2, expected_variance)
        c, s = core.aggregate(q, np.ones(3))
        self.assertEqual(c, q.mean())
        self.assertEqual(s, q.std())
        with self.assertRaises(ValueError):
            core.aggregate(q, np.array([1., 0., 1.]))

    def test_floor_handles_zero_and_constant_scores(self):
        for q in (np.zeros(20), np.ones(20)):
            _, scale = core.aggregate(q, np.power(.5, np.arange(20) / 20))
            self.assertEqual(scale, 1e-6)
        for bad in (np.full(20, np.nan), np.full(20, np.inf)):
            with self.assertRaises(ValueError):
                core.aggregate(bad, np.ones(20))

    def test_uniform_recovers_frozen_core_across_lengths_and_dimensions(self):
        rng = np.random.default_rng(91)
        for dimensions in (31, 47):
            for n in (20, 21, 49, 50):
                x = rng.uniform(.1, .3, (n, dimensions))
                before = x.copy()
                old_model, center, scale = fit_history(x, 'decay20')
                state = core.fit_shared(x)
                self.assertEqual(state.normalizers['uniform_cv'], (center, scale))
                np.testing.assert_array_equal(state.model.mean_, old_model.mean_)
                np.testing.assert_array_equal(state.model.mad_, old_model.mad_)
                self.assertFalse(state.oof_scores.flags.writeable)
                self.assertFalse(state.weights.flags.writeable)
                np.testing.assert_array_equal(x, before)

    def test_folds_fit_once_and_weights_keep_original_history_ages(self):
        x = np.arange(150.).reshape(50, 3)
        seen = []
        original = WeightedManhattan.fit

        def spy(model, train, weights):
            seen.append((train.copy(), weights.copy()))
            return original(model, train, weights)

        with patch.object(WeightedManhattan, 'fit', new=spy):
            state = core.fit_shared(x)
        self.assertEqual(len(seen), 6)  # Five CV fits + one final detector, not twice.
        for (train, weights), held in zip(seen[:5], np.array_split(np.arange(50), 5)):
            np.testing.assert_array_equal(train, np.delete(x, held, axis=0))
            np.testing.assert_array_equal(weights, np.delete(state.weights, held))
        np.testing.assert_array_equal(seen[-1][0], x)

    def test_one_raw_score_call_supplies_both_normalizations(self):
        state = core.fit_shared(toy()['0'][1])
        raw = np.array([30., 60., 90.])
        with patch.object(state.model, 'score', return_value=raw) as score:
            result = state.score_both(np.ones((3, 3)))
        score.assert_called_once()
        for arm in core.ARMS:
            center, scale = state.normalizers[arm]
            np.testing.assert_array_equal(result[arm], (raw - center) / scale)

    def test_joint_history_updates_all_genuine_and_never_probes(self):
        s1 = np.arange(180.).reshape(60, 3)
        s2 = np.array([[300., 301., 302.], [400., 401., 402.]])
        probes = np.full((10, 3), 9999.)
        histories = []

        class State:
            def score_both(self, rows):
                # Opposite decisions around tau=0 still must share all updates.
                return {'uniform_cv': np.full(len(rows), 1.), 'age_weighted_cv': np.full(len(rows), -1.)}

        def fit(history):
            histories.append(history.copy())
            return State()

        with patch.object(core, 'fit_shared', side_effect=fit):
            genuine, impostors = core.score_test_account(s1, s2, probes)
        self.assertEqual(len(histories), 3)
        self.assertTrue(all(len(h) == 50 for h in histories))
        np.testing.assert_array_equal(histories[0], s1[-50:])
        np.testing.assert_array_equal(histories[1][-1], s2[0])
        np.testing.assert_array_equal(histories[2][-1], s2[1])
        self.assertTrue(all(9999 not in h for h in histories))
        self.assertEqual(len(genuine['uniform_cv']), 2)
        self.assertEqual(len(impostors['age_weighted_cv']), 10)

    def test_future_samples_and_probes_do_not_change_past_genuine_scores(self):
        data = toy()
        s1, s2, probes = data['0'][1], data['0'][2], data['1'][2][:10]
        first, _ = core.score_test_account(s1, s2, probes)
        changed = s2.copy()
        changed[-1] += 100
        second, _ = core.score_test_account(s1, changed, probes + 900)
        for arm in core.ARMS:
            np.testing.assert_array_equal(first[arm][:-1], second[arm][:-1])

    def test_synthetic_pipeline_baseline_matches_saved_core_and_pairs(self):
        data = toy()
        before = copy.deepcopy(data)
        expected = validate_data(data, ['0', '1'], ['2', '3'], 3)
        with patch('keyguard.evaluation.threshold_at_far', side_effect=AssertionError('No threshold selection')):
            result = core.evaluate_dataset(data, ['0', '1'], ['2', '3'], 3, expected, .1)
        old = evaluate_test({p: data[p] for p in ['2', '3']}, 'decay20', {'threshold': .1})
        self.assertEqual(result['arms'][0]['overall'], old['overall'])
        self.assertEqual(result['arms'][0]['accounts'], old['accounts'])
        self.assertEqual(result['arms'][0]['pairs'], old['pairs'])
        for arm in result['arms']:
            self.assertEqual(arm['threshold'], .1)
            self.assertEqual(arm['observed_dev']['threshold'], .1)
            self.assertEqual(arm['overall']['genuine_trials'], 25)
            self.assertEqual(arm['overall']['impostor_trials'], 20)
        t = result['pair_transitions']
        self.assertEqual(sum(sum(r[k] for k in ('new_false_accept', 'recovered_rejection', 'accepted_both', 'rejected_both')) for r in t), 20)
        self.assertEqual(sum(r['new_false_accept'] - r['recovered_rejection'] for r in t),
                         result['arms'][1]['overall']['impostor_accepted'] - result['arms'][0]['overall']['impostor_accepted'])
        for pid in data:
            for session in (1, 2):
                np.testing.assert_array_equal(data[pid][session], before[pid][session])

    def test_dev_observation_has_no_access_to_s2_or_test_and_no_far_cap(self):
        data = toy()
        expected = validate_data(data, ['0', '1'], ['2', '3'], 3)
        first = core.evaluate_dataset(data, ['0', '1'], ['2', '3'], 3, expected, 1e9)
        changed = copy.deepcopy(data)
        for pid in ['0', '1']:
            changed[pid][2] += 700
        for pid in ['2', '3']:
            changed[pid][1] += 800
            changed[pid][2] += 900
        second = core.evaluate_dataset(changed, ['0', '1'], ['2', '3'], 3, expected, 1e9)
        self.assertEqual([a['observed_dev'] for a in first['arms']], [a['observed_dev'] for a in second['arms']])
        self.assertTrue(all(a['observed_dev']['far'] == 1. for a in first['arms']))

    def test_invalid_counts_stop_before_fit(self):
        with patch.object(core, 'fit_shared') as fit:
            with self.assertRaises(ValueError):
                core.evaluate_dataset(toy(), ['0', '1'], ['2', '3'], 3, {}, 0.)
            fit.assert_not_called()

    def test_far_first_decision_and_exact_small_increases(self):
        baseline = {'accounts': [account('a', 2, 10, 1, 10)]}
        candidate = {'accounts': [account('a', 1, 10, 1, 10)]}
        self.assertTrue(core.compare(baseline, candidate)['descriptive_support'])
        candidate['accounts'][0]['genuine_rejected'] = 2
        self.assertEqual(core.compare(baseline, candidate)['interpretation'], 'tradeoff')

        candidate['accounts'][0]['impostor_accepted'] = 2
        candidate['accounts'][0]['genuine_rejected'] = 0
        self.assertFalse(core.compare(baseline, candidate)['descriptive_support'])
        candidate['accounts'][0]['impostor_accepted'] = 1
        for row in (baseline['accounts'][0], candidate['accounts'][0]):
            row['genuine_trials'] = 10**9
        baseline['accounts'][0]['genuine_rejected'] = 0
        candidate['accounts'][0]['genuine_rejected'] = 1
        self.assertEqual(core.compare(baseline, candidate)['interpretation'], 'tradeoff')

    def test_macro_frr_is_not_replaced_by_pooled_frr(self):
        baseline = {'accounts': [account('a', 2, 10, 10, 10), account('b', 2, 10, 0, 100)]}
        candidate = {'accounts': [account('a', 1, 10, 0, 10), account('b', 1, 10, 30, 100)]}
        result = core.compare(baseline, candidate)
        self.assertAlmostEqual(result['delta_macro_frr'], -.35)
        self.assertTrue(result['descriptive_support'])  # Pooled FRR increases, macro decreases.


class ControlRunnerTest(unittest.TestCase):
    def test_cli_freeze_check_and_missing_mode_never_score(self):
        with patch.object(runner, 'freeze_runner') as freeze, patch.object(runner, 'check_freeze') as check, patch.object(
                runner, 'run_frozen') as run:
            runner.main(['--freeze'])
            runner.main(['--check'])
            freeze.assert_called_once()
            check.assert_called_once()
            with self.assertRaises(SystemExit):
                runner.main([])
            run.assert_not_called()

    def test_refreeze_and_partial_output_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(runner, 'load_plan') as load:
            root = Path(folder)
            (root / 'results').mkdir()
            p = root / runner.TESTS
            p.write_text('prior evidence')
            with self.assertRaises(RuntimeError):
                runner.freeze_runner(root)
            load.assert_not_called()
            (root / runner.OUTPUTS[0]).write_text('interrupted journal')
            with self.assertRaises(RuntimeError):
                runner.guard_outputs(root)
            self.assertEqual(p.read_text(), 'prior evidence')

    def test_missing_valid_freeze_blocks_data_loading(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(runner, 'check_freeze', side_effect=RuntimeError('Invalid')), patch.object(
                runner, 'load_inputs') as load:
            with self.assertRaises(RuntimeError):
                runner.run_frozen(Path(folder))
            load.assert_not_called()

    def test_baseline_mismatch_stops_interpretation(self):
        arm = {'threshold': .2, 'overall': {'genuine_rejected': 3}, 'accounts': [],
               'pairs': [], 'observed_dev': {'far': .05}}
        spec = {'shared_fixed_threshold': .2, 'baseline_expected_overall': arm['overall'],
                'baseline_expected_accounts': []}
        reference = {'pairs': [], 'calibration': {'far': .05}}
        runner.verify_baseline({'arms': [arm]}, spec, reference)
        wrong = copy.deepcopy(arm)
        wrong['overall']['genuine_rejected'] += 1
        with self.assertRaises(RuntimeError):
            runner.verify_baseline({'arms': [wrong]}, spec, reference)

    def test_code_environment_threshold_and_manifest_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'results').mkdir()
            (root / runner.PLAN).write_text('plan')
            for p in ('code', 'raw', 'tests'):
                (root / p).write_text(p)
            plan = {'protocol_sha256': 'protocol', 'datasets': [{'name': 'toy', 'shared_fixed_threshold': .1}]}
            freeze = {'plan_sha256': runner.sha(root / runner.PLAN), 'protocol_sha256': 'protocol',
                      'code_sha256': {'code': runner.sha(root / 'code')},
                      'raw_sha256': {'raw': runner.sha(root / 'raw')},
                      'synthetic_tests': {'file': 'tests', 'sha256': runner.sha(root / 'tests')},
                      'environment': {'v': 1}, 'thresholds': {'toy': .1}}
            runner.write_json_new(root / runner.FREEZE, freeze)
            (root / runner.FREEZE_SHA).write_text(runner.sha(root / runner.FREEZE))
            with patch.object(runner, 'load_plan', return_value=(plan, {})), patch.object(
                    runner, 'environment', return_value={'v': 1}):
                runner.check_freeze(root)
                (root / 'code').write_text('changed')
                with self.assertRaises(RuntimeError):
                    runner.check_freeze(root)
                (root / 'code').write_text('code')
                with patch.object(runner, 'environment', return_value={'v': 2}):
                    with self.assertRaises(RuntimeError):
                        runner.check_freeze(root)
                plan['datasets'][0]['shared_fixed_threshold'] = .2
                with self.assertRaises(RuntimeError):
                    runner.check_freeze(root)
                plan['datasets'][0]['shared_fixed_threshold'] = .1
                with (root / runner.FREEZE).open('a') as stream:
                    stream.write(' ')
                with self.assertRaises(RuntimeError):
                    runner.check_freeze(root)


if __name__ == '__main__':
    unittest.main()
