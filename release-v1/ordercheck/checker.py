"""Order completeness and strict value checks for the synthetic T03 lab.

T03 covers structural parsing, required fields, placeholders, and the value
rules in SPEC.md. Evidence verification and T04 packaging remain out of scope.
"""
import math
import re

FIELDS = ('Order ID', 'Revision', 'Product', 'Flow', 'Head', 'Material', 'Quantity')
PLACEHOLDERS = frozenset({'tbd', '待定'})
FLOW_UNIT = 'm3/h'
HEAD_UNIT = 'm'
QUANTITY_RE = re.compile(r'[0-9]+')


def _add_finding(findings, seen, field, code):
    marker = (field, code)
    if marker not in seen:
        seen.add(marker)
        findings.append({'field': field, 'code': code})


def _check_measure(value, expected_unit, field, add):
    parts = value.split()
    if len(parts) != 2:
        add(field, 'INVALID_VALUE')
        return
    number_text, unit = parts
    if unit != expected_unit:
        add(field, 'INVALID_UNIT')
        return
    try:
        number = float(number_text)
    except ValueError:
        add(field, 'INVALID_VALUE')
        return
    if not math.isfinite(number):
        add(field, 'NON_FINITE')
    elif number <= 0:
        add(field, 'NON_POSITIVE')


def _check_quantity(value, field, add):
    if QUANTITY_RE.fullmatch(value) is None:
        add(field, 'INVALID_QUANTITY')
        return
    try:
        quantity = int(value)
    except ValueError:
        add(field, 'INVALID_QUANTITY')
        return
    if quantity <= 0:
        add(field, 'INVALID_QUANTITY')


def check_order(text: str) -> dict:
    findings = []
    seen_findings = set()

    def add(field, code):
        _add_finding(findings, seen_findings, field, code)

    fields = {}
    seen_keys = set()
    reported_duplicates = set()
    reported_unknowns = set()

    # T03 structural pass: keep every non-empty line, report instead of dropping.
    for line_number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        if ':' not in line:
            add(f'<line {line_number}>', 'UNPARSABLE_LINE')
            continue
        key, value = (part.strip() for part in line.split(':', 1))
        display_field = key or '<empty key>'

        if key not in FIELDS and key not in reported_unknowns:
            reported_unknowns.add(key)
            add(display_field, 'UNKNOWN_FIELD')

        if key in seen_keys:
            if key not in reported_duplicates:
                reported_duplicates.add(key)
                add(display_field, 'DUPLICATE_FIELD')
        else:
            seen_keys.add(key)
            if key in FIELDS:
                fields[key] = value

    # T03 value pass: T02 presence/placeholder rules, then strict field rules.
    for key in FIELDS:
        value = fields.get(key, '')
        if not value or value.casefold() in PLACEHOLDERS:
            add(key, 'MISSING_FIELD')
            continue
        if key == 'Product':
            if value != 'Pump':
                add(key, 'INVALID_VALUE')
        elif key == 'Flow':
            _check_measure(value, FLOW_UNIT, key, add)
        elif key == 'Head':
            _check_measure(value, HEAD_UNIT, key, add)
        elif key == 'Quantity':
            _check_quantity(value, key, add)

    return {'decision': 'REVIEW' if findings else 'PASS', 'findings': findings}
