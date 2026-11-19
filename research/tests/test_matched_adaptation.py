"""Synthetic-only tests: no repository raw data, fitted real scores or freeze writes."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from keyguard import matched_adaptation as matched
from keyguard.session_adaptation import score_session_stream
from scripts import run_matched_adaptation as runner


def toy_data():
    rng = np.random.default_rng(71)
    return {str(i): {1: rng.uniform(.1, .3, (26, 2)),
                     2: rng.uniform(.1, .3, (10 + i, 2))} for i in range(4)}


def account(pid, rejected, genuine, accepted=0, impostors=10):
    return {'participant_id': pid, 'genuine_rejected': rejected,
            'genuine_trials': genuine, 'impostor_accepted': accepted,
            'impostor_trials': impostors}


class MatchedAdaptationTest(unittest.TestCase):
    def test_metadata_rejects_partition_overlap_duplicate_and_nonfinite(self):
        data = toy_data()
        for dev, test in [(['0', '1'], ['1', '2']), (['0', '0'], ['2', '3'])]:
            with self.assertRaises(ValueError):
                matched.validate_data(data, dev, test, 2)
        data['0'][1][0, 0] = np.nan
        with self.assertRaises(ValueError):
            matched.validate_data(data, ['0', '1'], ['2', '3'], 2)

    def test_metadata_rejects_extra_session_wrong_features_short_probe(self):
        for change in ('session', 'features', 'length'):
            data = toy_data()
            if change == 'session':
                data['0'][3] = data['0'][2]
            elif change == 'features':
                data['0'][1] = np.zeros((26, 3))
            else:
                data['3'][2] = data['3'][2][:9]
            with self.assertRaises(ValueError):
                matched.validate_data(data, ['0', '1'], ['2', '3'], 2)

    def test_count_mismatch_stops_before_any_fit(self):
        with patch.object(matched, 'fit_history') as fit:
            with self.assertRaises(ValueError):
                matched.run_dataset(toy_data(), ['0', '1'], ['2', '3'], 2, {})
            fit.assert_not_called()

    def test_probe_order_is_other_ids_first_five_last_five_no_self(self):
        values = {str(i): (np.arange(13) + 100 * i)[:, None] for i in range(3)}
        matrix, others = matched.probe_matrix(values, ['0', '1', '2'], '1')
        self.assertEqual(others, ['0', '2'])
        np.testing.assert_array_equal(matrix[:, 0], np.r_[np.arange(5), np.arange(8, 13),
                                                         np.arange(200, 205), np.arange(208, 213)])
        with self.assertRaises(ValueError):
            matched.probe_matrix({'a': np.zeros((9, 1)), 'b': np.zeros((9, 1))}, ['a', 'b'], 'a')

    def test_dev_fits_only_enrollment_and_ties_do_not_exceed_budget(self):
        s1 = {'a': np.ones((26, 2)), 'b': np.ones((30, 2))}
        actual = matched.fit_history
        seen = []

        def spy(x, method):
            seen.append(x.copy())
            return actual(x, method)

        with patch.object(matched, 'fit_history', side_effect=spy):
            result = matched.calibrate_dev(s1, 'window50')
        self.assertEqual([len(x) for x in seen], [20, 20])
        self.assertEqual(result['impostor_trials'], 20)
        self.assertEqual(result['impostor_accepted'], 0)
        self.assertLess(result['threshold'], 0)

    def test_both_calibrations_finish_before_test_and_only_receive_dev_s1(self):
        data = toy_data()
        expected = matched.validate_data(data, ['0', '1'], ['2', '3'], 2)
        events = []

        def calibrate(s1, method):
            events.append(('calibrate', method))
            self.assertEqual(list(s1), ['0', '1'])
            for pid in s1:
                self.assertIs(s1[pid], data[pid][1])
            return {'threshold': .2}

        def evaluate(test, method, calibration):
            events.append(('test', method))
            self.assertEqual(list(test), ['2', '3'])
            self.assertEqual(calibration, {'threshold': .2})
            return {'accounts': [account('2', 1, 12), account('3', 1, 13)]}

        with patch.object(matched, 'calibrate_dev', side_effect=calibrate), patch.object(
                matched, 'evaluate_test', side_effect=evaluate):
            matched.run_dataset(data, ['0', '1'], ['2', '3'], 2, expected)
        self.assertEqual(events, [('calibrate', 'window50'), ('calibrate', 'decay20'),
                                  ('test', 'window50'), ('test', 'decay20')])

    def test_score_before_update_warmup_window_and_probes_do_not_train(self):
        s1 = np.arange(80.)[:, None]
        s2 = np.array([[100.], [200.]])
        probes = np.full((10, 1), 9999.)
        histories = []

        class MeanScore:
            def __init__(self, x):
                self.center = x.mean()

            def score(self, x):
                return x[:, 0] - self.center

        def fit(history, method):
            histories.append(history.copy())
            return MeanScore(history), 0., 1.

        with patch.object(matched, 'fit_history', side_effect=fit):
            genuine, impostors = matched.score_account(s1, s2, probes, 'window50')
        self.assertEqual(len(histories), 3)
        self.assertTrue(all(len(h) == 50 for h in histories))
        np.testing.assert_array_equal(histories[0], s1[-50:])
        self.assertEqual(genuine[0], 100 - s1[-50:].mean())
        self.assertEqual(genuine[1], 200 - histories[1].mean())
        self.assertEqual(histories[1][-1, 0], 100)
        self.assertEqual(histories[2][-1, 0], 200)
        self.assertTrue(all(9999 not in h for h in histories))
        self.assertEqual(len(genuine), len(s2))
        self.assertEqual(len(impostors), 10)
        np.testing.assert_array_equal(s1[:, 0], np.arange(80.))

    def test_future_and_probe_changes_do_not_change_past_genuine_scores(self):
        data = toy_data()
        s1, s2 = data['0'][1], data['0'][2]
        probes = data['1'][2][:10]
        for method in matched.ARMS:
            first, _ = matched.score_account(s1, s2, probes, method)
            changed = s2.copy()
            changed[-1] += 100
            second, _ = matched.score_account(s1, changed, probes + 1000, method)
            np.testing.assert_array_equal(first[:-1], second[:-1])

    def test_warmup_shortcut_matches_existing_prequential_core(self):
        rng = np.random.default_rng(87)
        for dimensions in (31, 47):
            s1 = rng.uniform(.1, .3, (60, dimensions))
            s2 = rng.uniform(.1, .3, (10, dimensions))
            probes = rng.uniform(.1, .3, (20, dimensions))
            sessions = np.r_[np.ones(len(s1), dtype=int), np.full(len(s2), 2)]
            for method in matched.ARMS:
                old = score_session_stream(np.vstack((s1, s2)), sessions, probes, method)
                genuine, impostors = matched.score_account(s1, s2, probes, method)
                np.testing.assert_array_equal(genuine, [row['z'] for row in old['genuine'] if row['session'] == 2])
                np.testing.assert_array_equal(impostors, old['impostor'][-1]['scores'])

    def test_dev_threshold_invariant_to_dev_s2_and_all_test_values(self):
        data = toy_data()
        expected = matched.validate_data(data, ['0', '1'], ['2', '3'], 2)
        first = matched.run_dataset(data, ['0', '1'], ['2', '3'], 2, expected)
        changed = copy.deepcopy(data)
        for pid in ['0', '1']:
            changed[pid][2] += 123
        for pid in ['2', '3']:
            changed[pid][1] += 250
            changed[pid][2] *= 70
        second = matched.run_dataset(changed, ['0', '1'], ['2', '3'], 2, expected)
        self.assertEqual([a['calibration'] for a in first['arms']],
                         [a['calibration'] for a in second['arms']])

    def test_synthetic_end_to_end_counts_pairs_and_nonmutation(self):
        data = toy_data()
        before = copy.deepcopy(data)
        result = matched.run_dataset(data, ['0', '1'], ['2', '3'], 2,
                                     {'dev_impostor_trials': 20, 'test_genuine_trials': 25,
                                      'test_impostor_trials': 20})
        for arm in result['arms']:
            self.assertEqual(arm['overall']['genuine_trials'], 25)
            self.assertEqual(arm['overall']['impostor_trials'], 20)
            self.assertEqual(len(arm['pairs']), 2)
            self.assertEqual(sum(p['impostor_accepted'] for p in arm['pairs']),
                             arm['overall']['impostor_accepted'])
        for pid in data:
            for session in (1, 2):
                np.testing.assert_array_equal(data[pid][session], before[pid][session])

    def test_decision_uses_macro_not_pooled_and_keeps_small_far_increase(self):
        baseline = {'accounts': [account('a', 10, 10), account('b', 0, 100)]}
        candidate = {'accounts': [account('a', 0, 10), account('b', 30, 100)]}
        result = matched.compare_arms(baseline, candidate)
        self.assertAlmostEqual(result['delta_macro_frr'], -.35)
        self.assertTrue(result['descriptive_support'])  # Pooled FRR moves the opposite way.
        baseline['accounts'][0]['impostor_trials'] = 10**9
        candidate['accounts'][0]['impostor_trials'] = 10**9
        candidate['accounts'][0]['impostor_accepted'] = 1
        result = matched.compare_arms(baseline, candidate)
        self.assertEqual(result['interpretation'], 'tradeoff')
        self.assertGreater(result['delta_macro_far'], 0)

    def test_pairing_mismatch_rejected(self):
        left = {'accounts': [account('a', 0, 10)]}
        with self.assertRaises(ValueError):
            matched.compare_arms(left, {'accounts': [account('b', 0, 10)]})
        with self.assertRaises(ValueError):
            matched.compare_arms(left, {'accounts': [account('a', 0, 11)]})


class MatchedRunnerGuardTest(unittest.TestCase):
    def test_cli_check_and_freeze_never_route_to_scoring(self):
        with patch.object(runner, 'check_freeze') as check, patch.object(runner, 'freeze_runner') as freeze, patch.object(
                runner, 'run_frozen') as run:
            runner.main(['--check'])
            check.assert_called_once()
            runner.main(['--freeze'])
            freeze.assert_called_once()
            run.assert_not_called()
            with self.assertRaises(SystemExit):
                runner.main([])
            run.assert_not_called()

    def test_hash_guard_rejects_modified_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            p = root / 'code.py'
            p.write_text('version1')
            hashes = {'code.py': runner.sha(p)}
            runner.verify_hashes(root, hashes)
            p.write_text('version2')
            with self.assertRaises(RuntimeError):
                runner.verify_hashes(root, hashes)

    def test_output_guard_preserves_partial_or_existing_results(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'results').mkdir()
            p = root / runner.OUTPUTS[0]
            p.write_text('partial journal')
            with self.assertRaises(RuntimeError):
                runner.guard_new_outputs(root)
            self.assertEqual(p.read_text(), 'partial journal')
            with self.assertRaises(FileExistsError):
                runner.write_json_new(p, {'replace': True})

    def test_run_without_valid_freeze_stops_before_loading_data(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(
                runner, 'check_freeze', side_effect=RuntimeError('No valid freeze')), patch.object(
                runner, 'load_inputs') as load:
            with self.assertRaises(RuntimeError):
                runner.run_frozen(Path(folder))
            load.assert_not_called()

    def test_refreeze_is_rejected_before_tests_or_data_access(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(runner, 'load_plan') as load, patch.object(
                runner.subprocess, 'run') as tests:
            root = Path(folder)
            (root / 'results').mkdir()
            (root / runner.FREEZE).write_text('prior freeze')
            with self.assertRaises(RuntimeError):
                runner.freeze_runner(root)
            load.assert_not_called()
            tests.assert_not_called()
            self.assertEqual((root / runner.FREEZE).read_text(), 'prior freeze')

    def test_manifest_and_environment_changes_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'results').mkdir()
            for name in ('code', 'raw', 'tests'):
                (root / name).write_text(name)
            (root / runner.PLAN).write_text('plan')
            plan = {'protocol_sha256': 'protocol'}
            frozen = {'plan_sha256': runner.sha(root / runner.PLAN), 'protocol_sha256': 'protocol',
                      'code_sha256': {'code': runner.sha(root / 'code')},
                      'raw_sha256': {'raw': runner.sha(root / 'raw')},
                      'synthetic_tests': {'file': 'tests', 'sha256': runner.sha(root / 'tests')},
                      'environment': {'version': 1}}
            runner.write_json_new(root / runner.FREEZE, frozen)
            (root / runner.FREEZE_SHA).write_text(runner.sha(root / runner.FREEZE))
            with patch.object(runner, 'load_plan', return_value=plan), patch.object(
                    runner, 'environment', return_value={'version': 1}):
                runner.check_freeze(root)
                (root / 'code').write_text('changed')
                with self.assertRaises(RuntimeError):
                    runner.check_freeze(root)
                (root / 'code').write_text('code')
                with patch.object(runner, 'environment', return_value={'version': 2}):
                    with self.assertRaises(RuntimeError):
                        runner.check_freeze(root)
                with (root / runner.FREEZE).open('a') as stream:
                    stream.write(' ')
                with self.assertRaises(RuntimeError):
                    runner.check_freeze(root)


if __name__ == '__main__':
    unittest.main()
