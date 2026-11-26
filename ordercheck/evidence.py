"""Domain-agnostic evidence verification core (T03 training scope).

Binds a UTF-8 byte range to the SHA-256 digest of the whole raw document and
verifies that binding exactly. This is a training implementation, not a
production identity, storage or authorization system.
"""
import hashlib
import hmac

_POINTER_KEYS = ('document_id', 'source_digest', 'start', 'end', 'quote')
_DIGEST_HEX_LEN = 64


def _as_bytes(raw, error):
    if isinstance(raw, (bytes, bytearray)):
        return bytes(raw)
    raise error('raw must be bytes')


def _as_index(value, name):
    # bool subclasses int; True/False must never be accepted as byte offsets.
    if type(value) is not int:
        raise ValueError('%s must be an int' % name)
    return value


def make_pointer(document_id: str, raw: bytes, start: int, end: int) -> dict:
    """Bind raw[start:end] to the document digest and return a pointer.

    Raises ValueError for an illegal interval or non-bytes input and
    UnicodeError when raw[start:end] is not valid UTF-8.
    """
    if not isinstance(document_id, str):
        raise ValueError('document_id must be a str')
    data = _as_bytes(raw, ValueError)
    start = _as_index(start, 'start')
    end = _as_index(end, 'end')
    if not 0 <= start < end <= len(data):
        raise ValueError('byte interval must satisfy 0 <= start < end <= len(raw)')
    quote = data[start:end].decode('utf-8')
    return {
        'document_id': document_id,
        'source_digest': hashlib.sha256(data).hexdigest(),
        'start': start,
        'end': end,
        'quote': quote,
    }


def verify_pointer(document_id: str, raw: bytes, pointer: dict) -> str:
    """Return VERIFIED only when every binding matches exactly.

    REJECTED means the evidence does not match; UNVERIFIABLE means the input is
    malformed or cannot be decoded and therefore cannot be checked. Any
    unexpected exception is also reported as REJECTED, never as VERIFIED.
    """
    try:
        return _verify(document_id, raw, pointer)
    except Exception:  # fail closed: no exception may ever authorize evidence
        return 'REJECTED'


def _verify(document_id, raw, pointer):
    if not isinstance(document_id, str) or not isinstance(raw, (bytes, bytearray)):
        return 'UNVERIFIABLE'
    if not isinstance(pointer, dict):
        return 'UNVERIFIABLE'
    if any(key not in pointer for key in _POINTER_KEYS):
        return 'UNVERIFIABLE'

    data = bytes(raw)

    if not isinstance(pointer['document_id'], str) or pointer['document_id'] != document_id:
        return 'REJECTED'

    digest = pointer['source_digest']
    if not isinstance(digest, str) or len(digest) != _DIGEST_HEX_LEN:
        return 'REJECTED'
    if not hmac.compare_digest(digest, hashlib.sha256(data).hexdigest()):
        return 'REJECTED'

    start, end = pointer['start'], pointer['end']
    if type(start) is not int or type(end) is not int:
        return 'REJECTED'
    if not 0 <= start < end <= len(data):
        return 'REJECTED'

    quote = pointer['quote']
    if not isinstance(quote, str) or not quote:
        return 'REJECTED'

    try:
        actual = data[start:end].decode('utf-8')
    except UnicodeDecodeError:
        return 'UNVERIFIABLE'
    return 'VERIFIED' if quote == actual else 'REJECTED'
