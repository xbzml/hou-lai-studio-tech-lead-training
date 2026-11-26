"""Training implementation: T02 required-field checks only; T03/T04 are incomplete."""
FIELDS = ('Order ID', 'Revision', 'Product', 'Flow', 'Head', 'Material', 'Quantity')
PLACEHOLDERS = frozenset({'tbd', '待定'})


def check_order(text: str) -> dict:
    fields = dict(tuple(p.strip() for p in line.split(':', 1))
                  for line in text.splitlines() if ':' in line)
    findings = []
    # T02 only: presence, blank values, and placeholders. Strict parsing and
    # value validation belong to T03.
    for key in FIELDS:
        value = fields.get(key, '').strip()
        if not value or value.casefold() in PLACEHOLDERS:
            findings.append({'field': key, 'code': 'MISSING_FIELD'})
    return {'decision': 'REVIEW' if findings else 'PASS', 'findings': findings}
