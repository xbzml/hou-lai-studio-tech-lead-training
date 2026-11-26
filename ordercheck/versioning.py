"""Bind check results to a document ID and raw-content SHA-256 (T03).

Typical use::

    raw = path.read_bytes()
    result = check_order(raw.decode('utf-8'))
    binding = bind_result(document_id, raw, result)

    status = verify_binding(document_id, raw, binding)
    if status == STALE:
        result = check_order(raw.decode('utf-8'))
        binding = bind_result(document_id, raw, result)

The payload is an opaque dict; this module does not reference OrderCheck field
names and does not import the evidence module.
"""
import copy
import hashlib
import re

_DIGEST_RE = re.compile(r'[0-9a-f]{64}')

CURRENT = 'CURRENT'
STALE = 'STALE'
MISMATCH = 'MISMATCH'
UNVERIFIABLE = 'UNVERIFIABLE'


def bind_result(document_id: str, raw: bytes, result: dict) -> dict:
    """Return a binding for a result and the exact raw bytes it describes."""
    if not isinstance(document_id, str) or not document_id:
        raise ValueError('document_id must be a non-empty str')
    if not isinstance(raw, bytes):
        raise TypeError('raw must be bytes')
    if not isinstance(result, dict):
        raise TypeError('result must be a dict')
    return {
        'document_id': document_id,
        'source_digest': hashlib.sha256(raw).hexdigest(),
        'result': copy.deepcopy(result),
    }


def verify_binding(document_id: str, raw: bytes, binding: dict) -> str:
    """Return CURRENT, STALE, MISMATCH or UNVERIFIABLE.

    CURRENT: document ID and SHA-256 both match; the bound result applies.
    STALE: same document, but raw bytes changed; re-run the check.
    MISMATCH: the binding belongs to a different document.
    UNVERIFIABLE: malformed input; never treated as current.
    """
    try:
        if (not isinstance(document_id, str) or not document_id
                or not isinstance(raw, bytes)
                or not isinstance(binding, dict)):
            return UNVERIFIABLE
        bound_id = binding.get('document_id')
        digest = binding.get('source_digest')
        if (not isinstance(bound_id, str) or not bound_id
                or not isinstance(digest, str)
                or _DIGEST_RE.fullmatch(digest) is None
                or not isinstance(binding.get('result'), dict)):
            return UNVERIFIABLE
        if bound_id != document_id:
            return MISMATCH
        if digest != hashlib.sha256(raw).hexdigest():
            return STALE
        return CURRENT
    except Exception:
        return UNVERIFIABLE
