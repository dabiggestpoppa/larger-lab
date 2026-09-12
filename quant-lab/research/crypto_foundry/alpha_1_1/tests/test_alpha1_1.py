"""Tests for CRYPTO-ALPHA-1.1 — Contract Integrity & Backtest Readiness Seal."""
import csv, hashlib, json, sys, unittest
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
A11 = HERE.parent
A1 = A11.parent / 'alpha_1'
M2 = A1.parent / 'mech_2'
SEED = 31082026

def jl(p): return json.load(open(p, encoding='utf-8'))

class TestDataSplit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = jl(A11 / 'ALPHA_1_1_DATA_SPLIT_CONTRACT.json')
        cls.ds_a1 = jl(A1 / 'ALPHA_1_DATA_SPLIT_CONTRACT.json')

    def test_no_impossible_dates(self):
        for name, period in self.ds['periods'].items():
            start = period['start']
            end = period['end']
            self.assertLessEqual(start, end, f'{name}: start={start} > end={end}')

    def test_confirmation_deferred(self):
        self.assertFalse(self.ds['untouched_confirmation']['available'])
        self.assertEqual(self.ds['forward_confirmation']['status'], 'DEFERRED_TO_FUTURE_DATA')

    def test_canonical_alpha1_updated(self):
        self.assertIn('research_consumed', self.ds_a1['periods'])

class TestCoverageMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cov = list(csv.DictReader(open(A11 / 'ALPHA_1_1_STATE_COVERAGE_MATRIX.csv', encoding='utf-8')))

    def test_all_25_states_present(self):
        self.assertEqual(len(self.cov), 25)

    def test_each_state_has_status(self):
        for r in self.cov:
            self.assertIn(r['coverage_status'], ['DIRECTLY_CONSUMED', 'CONTROL_ONLY', 'DESIGN_REJECTED_WITH_REASON'])

    def test_fam_c_normal_basis_rejected(self):
        for r in self.cov:
            if 'B0_NORMAL' in r['state_value'] and 'FAM_C' in r['family_id']:
                self.assertIn('REJECTED', r['coverage_status'],
                              f'{r["source_state_id"]} should be rejected from FAM_C')
    
    def test_systemic_stress_rejected(self):
        for r in self.cov:
            if 'SYSTEMIC_STRESS' in r['state_value']:
                self.assertIn('REJECTED', r['coverage_status'])

class TestStrategyContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contracts = jl(A1 / 'ALPHA_1_STRATEGY_CONTRACTS.json')

    def test_all_have_control_id(self):
        for c in self.contracts:
            self.assertIn('control_id', c)
    
    def test_s011_is_exploratory(self):
        s011 = [c for c in self.contracts if c['strategy_id'] == 'ALPHA1_S011'][0]
        self.assertEqual(s011['variant_type'], 'EXPLORATORY_EXPRESSION')

    def test_all_have_direction_evidence(self):
        for c in self.contracts:
            self.assertIn('direction_evidence', c)
            self.assertIn('moving_leg', c)
            self.assertIn('alt_risk', c)

    def test_s009_s010_no_systemic(self):
        for sid in ('ALPHA1_S009', 'ALPHA1_S010'):
            c = [x for x in self.contracts if x['strategy_id'] == sid][0]
            self.assertNotIn('SYSTEMIC', str(c['source_state_ids']))
            self.assertNotIn('SYSTEMIC_STRESS', c['entry_state'])

    def test_exit_precedence_frozen(self):
        for c in self.contracts:
            self.assertIn('exit_precedence', c)

    def test_no_pnl_fields(self):
        forbidden = ['sharpe', 'profit_factor', 'win_rate', 'pnl', 'backtest_result']
        for c in self.contracts:
            c_str = json.dumps(c).lower()
            for word in forbidden:
                self.assertNotIn(word, c_str, f'{c["strategy_id"]} contains {word}')

class TestThresholdContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tc = jl(A11 / 'ALPHA_1_1_THRESHOLD_CONTRACT.json')

    def test_both_assets_present(self):
        for a in ['BTC', 'ETH']:
            self.assertIn(a, self.tc)
            self.assertIn('basis', self.tc[a])
            self.assertIn('funding', self.tc[a])
            self.assertIn('vol_rv24', self.tc[a])

    def test_thresholds_are_numeric(self):
        for a in ['BTC', 'ETH']:
            for cat in ['basis', 'funding', 'vol_rv24']:
                for k, v in self.tc[a][cat].items():
                    self.assertIsInstance(v, (int, float)), f'{a}.{cat}.{k} not numeric'

class TestControlSampling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cs = jl(A11 / 'ALPHA_1_1_CONTROL_SAMPLING_CONTRACT.json')

    def test_seed_frozen(self):
        self.assertEqual(self.cs['seed'], SEED)

    def test_draws_defined(self):
        self.assertGreater(self.cs['draws_per_event'], 0)

class TestFundingContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fc = jl(A11 / 'ALPHA_1_1_FUNDING_ACCOUNTING_CONTRACT.json')

    def test_settlement_timing(self):
        self.assertIn('settlements', self.fc)
        self.assertIn('entry_on_settlement', self.fc)
        self.assertIn('exit_on_settlement', self.fc)

class TestCostContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cc = jl(A11 / 'ALPHA_1_1_COST_ACCOUNTING_CONTRACT.json')

    def test_one_way_convention(self):
        self.assertIn('ONE-WAY', self.cc['convention'])

    def test_perp_roundtrip_positive(self):
        self.assertGreater(self.cc['perp_roundtrip_bps'], 0)
        self.assertGreater(self.cc['stress_2x']['perp'], self.cc['perp_roundtrip_bps'])

class TestExecutionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ec = jl(A11 / 'ALPHA_1_1_EXECUTION_CONTRACT.json')

    def test_no_same_bar(self):
        self.assertTrue(self.ec['no_same_bar'])

    def test_signal_collision(self):
        self.assertEqual(self.ec['signal_collision'], 'IGNORE_NEW_SIGNAL')

class TestBacktestContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bc = jl(A11 / 'ALPHA_1_1_BACKTEST_CONTRACT.json')

    def test_no_production_classes(self):
        for nc in self.bc['no_classes']:
            self.assertNotIn(nc, self.bc['result_classes'])

class TestFalsificationRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fr = jl(A1 / 'ALPHA_1_FALSIFICATION_RULES.json')

    def test_f8_has_bootstrap(self):
        f8 = [r for r in self.fr['rules'] if r['rule_id'] == 'F8']
        self.assertEqual(len(f8), 1)
        self.assertEqual(f8[0]['method'], 'paired_bootstrap_difference')
        self.assertEqual(f8[0]['seed'], SEED)

    def test_f2_is_flag(self):
        f2 = [r for r in self.fr['rules'] if r['rule_id'] == 'F2'][0]
        self.assertIn('FLAG', f2['condition'])

class TestRegistryHash(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hd = jl(A1 / 'ALPHA_1_STRATEGY_REGISTRY_HASH.json')
        cls.contracts = jl(A1 / 'ALPHA_1_STRATEGY_CONTRACTS.json')

    def test_hash_matches_contracts(self):
        payload = json.dumps(self.contracts, sort_keys=True, ensure_ascii=False)
        expected = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        self.assertEqual(self.hd['new_registry_hash'], expected)

    def test_no_results_seen(self):
        self.assertTrue(self.hd['no_results_seen'])

    def test_old_hash_recorded(self):
        self.assertIn('old_hash', self.hd)

class TestNoPnL(unittest.TestCase):
    def test_all_artifacts_no_pnl(self):
        forbidden = ['sharpe', 'win_rate_percent', 'max_drawdown_percent',
                     'expectancy', 'total_profit', 'pnl_observed_as_true']
        for p in A11.glob('*.json'):
            text = json.dumps(jl(p)).lower()
            for w in forbidden:
                self.assertNotIn(w, text, f'{p.name} contains {w}')

if __name__ == '__main__':
    unittest.main()