import json
import sys
from pathlib import Path

from .checker import check_order

EXIT_CODES = {'PASS': 0, 'REVIEW': 1, 'BLOCK': 2}
INPUT_FIELD = '<input>'


def _block(code):
    return {'decision': 'BLOCK', 'findings': [{'field': INPUT_FIELD, 'code': code}]}


def main():
    if len(sys.argv) != 2:
        print('Usage: python -m ordercheck FILE', file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if path.suffix.lower() != '.txt':
        result = _block('UNSUPPORTED_FORMAT')
    else:
        try:
            raw = path.read_bytes()
            result = check_order(raw.decode('utf-8'))
        except UnicodeDecodeError:
            result = _block('INVALID_ENCODING')
        except OSError:
            result = _block('INPUT_UNREADABLE')
        except Exception:
            result = _block('EXECUTION_ERROR')

    print(json.dumps(result, ensure_ascii=False))
    return EXIT_CODES.get(result.get('decision'), 2)


if __name__ == '__main__':
    raise SystemExit(main())
