"""T02 contract tests plus the T03 strictness that supersedes T02 boundaries.

T02 expectations remain for required fields, blank values, and placeholders.
The former "T02 scope boundary" test was replaced by T03Strictness because the
final contract is T03.
"""
import unittest
from pathlib import Path

from ordercheck.checker import check_order

FIX = Path(__file__).resolve().parents[1] / 'fixtures'
FIELDS = ('Order ID', 'Revision', 'Product', 'Flow', 'Head', 'Material', 'Quantity')
PLACEHOLDER_VALUES = ('TBD', 'tbd', 'Tbd', '待定', ' tbd ')


def baseline_lines():
    return (FIX / 'order_ok.txt').read_text(encoding='utf-8').splitlines()


def build_text(remove=(), overrides=None):
    """Build a synthetic order, removing or replacing fields in the baseline."""
    remove = set(remove)
    overrides = overrides or {}
    lines = []
    for line in baseline_lines():
        key = line.split(':', 1)[0].strip()
        if key in remove:
            continue
        if key in overrides:
            lines.append(f'{key}: {overrides[key]}')
        else:
            lines.append(line)
    return '\n'.join(lines) + '\n'


class T02Contract(unittest.TestCase):
    def assert_review(self, text, expected_fields):
        result = check_order(text)
        self.assertEqual(result['decision'], 'REVIEW')
        self.assertEqual([f['field'] for f in result['findings']], list(expected_fields))
        for finding in result['findings']:
            self.assertEqual(set(finding), {'field', 'code'})
            self.assertEqual(finding['code'], 'MISSING_FIELD')

    def test_normal_order_passes_without_findings(self):
        result = check_order((FIX / 'order_ok.txt').read_text(encoding='utf-8'))
        self.assertEqual(result['decision'], 'PASS')
        self.assertEqual(result['findings'], [])

    def test_each_required_field_missing(self):
        for field in FIELDS:
            with self.subTest(field=field):
                self.assert_review(build_text(remove=(field,)), (field,))

    def test_each_required_field_blank(self):
        for field in FIELDS:
            for blank in ('', '   '):
                with self.subTest(field=field, blank=repr(blank)):
                    self.assert_review(build_text(overrides={field: blank}), (field,))

    def test_placeholders_rejected_in_every_required_field(self):
        for field in FIELDS:
            for value in PLACEHOLDER_VALUES:
                with self.subTest(field=field, value=value):
                    self.assert_review(build_text(overrides={field: value}), (field,))

    def test_multiple_missing_fields_keep_contract_order(self):
        self.assert_review(build_text(remove=('Material', 'Quantity')),
                           ('Material', 'Quantity'))
        self.assert_review(build_text(overrides={'Revision': 'TBD', 'Product': ' '}),
                           ('Revision', 'Product'))

    def test_order_missing_fixture_now_reviews(self):
        text = (FIX / 'order_missing.txt').read_text(encoding='utf-8')
        self.assert_review(text, ('Material',))

    def test_values_containing_placeholder_text_are_not_rejected(self):
        for value in ('TBD-grade', '待定材料', 'TBD-001'):
            with self.subTest(value=value):
                result = check_order(build_text(overrides={'Material': value}))
                self.assertEqual(result['decision'], 'PASS')
                self.assertEqual(result['findings'], [])

    def test_decision_vocabulary_is_t02_only(self):
        for text in (build_text(), build_text(remove=('Material',))):
            self.assertIn(check_order(text)['decision'], {'PASS', 'REVIEW'})


class T03Strictness(unittest.TestCase):
    """T03 supersedes the former T02 scope boundary with strict checks."""

    def test_structure_errors_are_reported(self):
        cases = (
            (build_text() + 'Material: 304L\n', 'Material', 'DUPLICATE_FIELD'),
            (build_text() + 'Price: 100\n', 'Price', 'UNKNOWN_FIELD'),
        )
        for text, field, code in cases:
            with self.subTest(code=code):
                result = check_order(text)
                self.assertEqual(result['decision'], 'REVIEW')
                self.assertIn({'field': field, 'code': code}, result['findings'])

        result = check_order(build_text() + 'no colon here\n')
        self.assertEqual(result['decision'], 'REVIEW')
        self.assertTrue(any(f['code'] == 'UNPARSABLE_LINE' for f in result['findings']))

    def test_duplicate_key_cannot_mask_placeholder(self):
        text = build_text().replace('Material: 316L\n',
                                    'Material: TBD\nMaterial: 316L\n')
        result = check_order(text)
        self.assertEqual(result['decision'], 'REVIEW')
        self.assertIn({'field': 'Material', 'code': 'DUPLICATE_FIELD'},
                      result['findings'])
        self.assertIn({'field': 'Material', 'code': 'MISSING_FIELD'},
                      result['findings'])

    def test_value_rules_are_enforced(self):
        cases = (
            ('Product', 'Valve', 'INVALID_VALUE'),
            ('Product', 'pump', 'INVALID_VALUE'),
            ('Flow', '50', 'INVALID_VALUE'),
            ('Flow', '50 L/s', 'INVALID_UNIT'),
            ('Flow', '-50 m3/h', 'NON_POSITIVE'),
            ('Flow', 'nan m3/h', 'NON_FINITE'),
            ('Head', '30 cm', 'INVALID_UNIT'),
            ('Quantity', '5.5', 'INVALID_QUANTITY'),
            ('Quantity', '0', 'INVALID_QUANTITY'),
            ('Quantity', '-3', 'INVALID_QUANTITY'),
            ('Quantity', '5 pcs', 'INVALID_QUANTITY'),
        )
        for field, value, code in cases:
            with self.subTest(field=field, value=value):
                result = check_order(build_text(overrides={field: value}))
                self.assertEqual(result['decision'], 'REVIEW')
                self.assertIn({'field': field, 'code': code}, result['findings'])


if __name__ == '__main__':
    unittest.main()
