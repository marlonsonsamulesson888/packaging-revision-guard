"""Read-only, two-file sample identity manifest; no visual/content verdict."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def inspect(path):
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError('input must be a regular non-symlink file')
    before = p.stat()
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    after = p.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('input changed during hashing')
    return {'bytes': after.st_size, 'sha256': h.hexdigest()}


def compare(a, b):
    first, second = inspect(a), inspect(b)
    return {'A': first, 'B': second, 'same_file': Path(a).samefile(b),
            'same_bytes': first == second,
            'scope': 'supplied file bytes only; not visual, version-origin, or print approval'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('A')
    parser.add_argument('B')
    args = parser.parse_args()
    try:
        result = compare(args.A, args.B)
    except (OSError, ValueError):
        print(json.dumps({'error': 'inputs unreadable, non-regular, or changed during hashing'}))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
