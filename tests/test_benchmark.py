import unittest
from benchmark import make_episode, run_policy, run_experiment
from pathlib import Path
import tempfile

class PaginationBenchmarkTests(unittest.TestCase):
    def episode(self, scenario):
        # Find a deterministic seed/index pair with the requested scenario.
        for seed in range(1, 100):
            for idx in range(100):
                ep = make_episode(seed, idx)
                if ep['scenario'] == scenario:
                    return ep
        self.fail('scenario not generated: ' + scenario)

    def test_stable_count_verified_completes(self):
        ep = self.episode('stable')
        row = run_policy(ep, 'count_verified')
        self.assertEqual(row['actual_complete'], 1)
        self.assertEqual(row['reported_complete'], 1)

    def test_empty_nonterminal_is_not_end_of_collection(self):
        ep = self.episode('empty_nonterminal')
        self.assertEqual(run_policy(ep, 'stop_on_empty')['false_completion'], 1)
        self.assertEqual(run_policy(ep, 'count_verified')['reported_complete'], 1)

    def test_duplicate_omission_detected_by_count(self):
        ep = self.episode('duplicate_omission')
        self.assertEqual(run_policy(ep, 'follow_cursor')['false_completion'], 1)
        self.assertEqual(run_policy(ep, 'count_verified')['reported_complete'], 0)

    def test_missing_page_detected_by_count(self):
        ep = self.episode('missing_page')
        self.assertEqual(run_policy(ep, 'count_verified')['reported_complete'], 0)

    def test_cursor_cycle_terminates_safely(self):
        ep = self.episode('cursor_cycle')
        row = run_policy(ep, 'count_verified', max_calls=100)
        self.assertEqual(row['termination'], 'cursor_cycle')
        self.assertEqual(row['reported_complete'], 0)
        self.assertLessEqual(row['calls'], len(ep['pages']))

    def test_first_page_policy_is_not_a_valid_completion_claim(self):
        ep = self.episode('stable')
        row = run_policy(ep, 'first_page_only')
        self.assertEqual(row['reported_complete'], 1)
        self.assertEqual(row['false_completion'], 1)

    def test_deterministic_generation(self):
        self.assertEqual(make_episode(17, 3), make_episode(17, 3))

    def test_experiment_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary = run_experiment(tmp, n_per_seed=5, seeds=(17,))
            self.assertEqual(summary['n_episodes'], 5)
            self.assertTrue((Path(tmp) / 'policy_metrics.csv').exists())
            self.assertTrue((Path(tmp) / 'per_episode_results.csv').exists())

if __name__ == '__main__':
    unittest.main()
