"""Deliberately weak training implementation; do not use in production."""
import hashlib


def make_pointer(document_id: str, raw: bytes, start: int, end: int) -> dict:
    return {'document_id': document_id, 'source_digest': hashlib.sha256(raw).hexdigest(),
            'start': start, 'end': end, 'quote': raw[start:end].decode('utf-8')}


def verify_pointer(document_id: str, raw: bytes, pointer: dict) -> str:
    # Intentionally incomplete: use SPEC as the source of truth.
    return 'VERIFIED' if pointer['quote'].encode('utf-8') in raw else 'REJECTED'
