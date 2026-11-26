"""T02 验收测试：必填字段完整性与占位符（学员可见的公开测试）。

预期结果只来自 SPEC.md 的「业务边界」键表与「T02 最小要求」，
不按 ordercheck 当前实现反推。刻意不覆盖 T03 的严格解析、
单位与数值合法性、重复/未知键、编码与 CLI 退出码、证据核验。

当前 starter 是故意不完整的训练起点，本文件在 starter 上大面积失败
属于预期（见 创始人专用/初始项目自检.md），不是测试写错。

运行（在训练项目根目录）：
    python -m unittest discover -s tests -p 'test_t02_completeness.py' -v
"""

import unittest

from ordercheck.checker import check_order

# SPEC「业务边界」：7 个必填键
FIELDS = (
    'Order ID',
    'Revision',
    'Product',
    'Flow',
    'Head',
    'Material',
    'Quantity',
)

# 全部字段合法时的一个订单；值本身取自 SPEC 键表要求
GOOD_VALUES = {
    'Order ID': 'SYN-001',
    'Revision': '1',
    'Product': 'Pump',
    'Flow': '50 m3/h',
    'Head': '30 m',
    'Material': '316L',
    'Quantity': '5',
}

# SPEC「T02 最小要求」：占位符忽略大小写与首尾空白
PLACEHOLDERS = ('TBD', 'tbd', 'Tbd', ' TBD ', '待定', ' 待定 ')

# SPEC：空值检查（含只有空白的值）
BLANKS = ('', '   ')


def build(**overrides):
    """按 FIELDS 顺序拼出订单文本；值为 None 表示整行缺失。"""
    lines = []
    for name in FIELDS:
        value = overrides.get(name, GOOD_VALUES[name])
        if value is None:
            continue
        lines.append('%s: %s' % (name, value))
    return '\n'.join(lines) + '\n'


class T02Completeness(unittest.TestCase):
    """T02 只判断三件事：字段是否齐全、是否空值、是否占位符。"""

    def assert_review_with(self, result, expected_fields):
        """REVIEW + findings 结构合法 + 每个期望字段各出现一条 MISSING_FIELD。

        子集匹配：实现额外报出别的 finding 不判失败（T03 会引入更多错误码）。
        """
        self.assertIsInstance(result, dict)
        self.assertIn('decision', result)
        self.assertIn('findings', result)
        self.assertEqual(result['decision'], 'REVIEW')

        findings = result['findings']
        self.assertIsInstance(findings, list)
        for item in findings:
            self.assertIsInstance(item, dict)
            self.assertIn('field', item)
            self.assertIn('code', item)
            self.assertIsInstance(item['field'], str)
            self.assertIsInstance(item['code'], str)
            self.assertIn(item['field'], FIELDS, 'finding 的 field 必须是 7 个必填键之一')

        got = {(item['field'], item['code']) for item in findings}
        for name in expected_fields:
            self.assertIn(
                (name, 'MISSING_FIELD'),
                got,
                '期望 %r 报 MISSING_FIELD，实际 findings=%r' % (name, findings),
            )

    # A 正常订单 --------------------------------------------------------
    def test_normal_order_passes(self):
        result = check_order(build())
        self.assertEqual(result['decision'], 'PASS')
        leaked = [i for i in result['findings'] if i.get('code') == 'MISSING_FIELD']
        self.assertEqual(leaked, [], '正常订单不应出现 MISSING_FIELD：%r' % (leaked,))

    # B 七个必填字段分别缺失 --------------------------------------------
    def test_each_required_field_missing(self):
        for name in FIELDS:
            with self.subTest(field=name):
                self.assert_review_with(check_order(build(**{name: None})), (name,))

    # C 七个字段分别为空白 ----------------------------------------------
    def test_each_required_field_blank(self):
        for name in FIELDS:
            for blank in BLANKS:
                with self.subTest(field=name, value=repr(blank)):
                    self.assert_review_with(check_order(build(**{name: blank})), (name,))

    # D 七个字段分别为占位符 --------------------------------------------
    def test_each_required_field_placeholder(self):
        for name in FIELDS:
            for value in PLACEHOLDERS:
                with self.subTest(field=name, value=value):
                    self.assert_review_with(check_order(build(**{name: value})), (name,))

    # E 多个必填字段同时缺失 --------------------------------------------
    def test_multiple_required_fields_missing(self):
        cases = (
            ('Material', 'Quantity'),
            ('Order ID', 'Flow', 'Head'),
            FIELDS,
        )
        for missing in cases:
            with self.subTest(missing=missing):
                text = build(**{name: None for name in missing})
                self.assert_review_with(check_order(text), missing)

    # E' 全部缺失：空内容与只有空白行 -----------------------------------
    def test_all_fields_missing(self):
        for text in ('', '\n', '\n\n'):
            with self.subTest(text=repr(text)):
                self.assert_review_with(check_order(text), FIELDS)

    # F findings 必须指名 field 与 MISSING_FIELD ------------------------
    def test_findings_name_the_missing_field(self):
        for name in FIELDS:
            with self.subTest(field=name):
                result = check_order(build(**{name: None}))
                self.assertEqual(result['decision'], 'REVIEW')
                findings = result['findings']
                self.assertTrue(findings, '字段缺失必须至少产生一条 finding')
                for item in findings:
                    self.assertIn('field', item)
                    self.assertIn('code', item)
                self.assertIn(
                    (name, 'MISSING_FIELD'),
                    {(i['field'], i['code']) for i in findings},
                    '缺失字段 %r 未被明确指名' % (name,),
                )


if __name__ == '__main__':
    unittest.main()
