import json
import sys
from pathlib import Path
from .checker import check_order


def main():
    if len(sys.argv) != 2:
        print('Usage: python -m ordercheck FILE', file=sys.stderr)
        return 2
    result = check_order(Path(sys.argv[1]).read_text(encoding='utf-8'))
    print(json.dumps(result, ensure_ascii=False))
    return {'PASS': 0, 'REVIEW': 1, 'BLOCK': 2}[result['decision']]


if __name__ == '__main__':
    raise SystemExit(main())
