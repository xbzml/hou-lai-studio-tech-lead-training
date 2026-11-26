"""Show T03 result binding for the release-v1 demo."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ordercheck.checker import check_order
from ordercheck.versioning import bind_result, verify_binding

raw = (ROOT / 'demo' / 'order_ok.txt').read_bytes()
result = check_order(raw.decode('utf-8'))
binding = bind_result('SYN-001', raw, result)

print('bound decision :', result['decision'])
print('same bytes     :', verify_binding('SYN-001', raw, binding))
print('changed bytes  :', verify_binding('SYN-001', raw.replace(b'316L', b'304L'), binding))
print('other doc id   :', verify_binding('OTHER', raw, binding))
print('malformed      :', verify_binding('SYN-001', raw, {'document_id': 'SYN-001'}))
