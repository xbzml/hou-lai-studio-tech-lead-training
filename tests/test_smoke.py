import unittest
from pathlib import Path
from ordercheck.checker import check_order
from ordercheck.evidence import make_pointer, verify_pointer

FIX = Path(__file__).resolve().parents[1] / 'fixtures'

class Smoke(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(check_order((FIX/'order_ok.txt').read_text())['decision'], 'PASS')
    def test_missing_quantity(self):
        text = (FIX/'order_ok.txt').read_text().replace('Quantity: 5', '')
        self.assertEqual(check_order(text)['decision'], 'REVIEW')
    def test_simple_pointer(self):
        raw = b'Flow: 50 m3/h'
        p = make_pointer('D1', raw, 6, len(raw))
        self.assertEqual(verify_pointer('D1', raw, p), 'VERIFIED')

if __name__ == '__main__':
    unittest.main()
