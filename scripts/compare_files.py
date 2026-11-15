#!/usr/bin/env python3
"""Read-only file-level revision check; no visual/semantic certification."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys


def inventory(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Input must be an existing non-symlink directory')
    records = {}
    def visit(folder):
        for entry in sorted(os.scandir(folder), key=lambda e: e.name):
            p = Path(entry.path)
            rel = p.relative_to(root).as_posix()
            mode = entry.stat(follow_symlinks=False).st_mode
            if stat.S_ISLNK(mode):
                raise ValueError('Symlinks are not supported')
            if stat.S_ISDIR(mode):
                visit(p)
            elif stat.S_ISREG(mode):
                h = hashlib.sha256()
                with p.open('rb') as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                        h.update(chunk)
                records[rel] = h.hexdigest()
            else:
                raise ValueError('Special files are not supported')
    visit(root)
    return records


def compare(before, after, allowed=()):
    allowed = set(allowed)
    for name in allowed:
        p = PurePosixPath(name)
        if not name or p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name or str(p) != name:
            raise ValueError('Allow paths must be normalized relative POSIX paths')
    a, b = inventory(before), inventory(after)
    changes = []
    for path in sorted(a.keys() | b.keys()):
        if a.get(path) == b.get(path):
            continue
        changes.append({'path': path, 'kind': 'added' if path not in a else 'removed' if path not in b else 'changed',
                        'allowed_file': path in allowed, 'before_sha256': a.get(path), 'after_sha256': b.get(path)})
    return {'scope': 'file-bytes-only', 'design_acceptance': 'not-assessed',
            'counts': {'before': len(a), 'after': len(b)}, 'changes': changes,
            'unexpected_changes': sum(not c['allowed_file'] for c in changes)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before')
    parser.add_argument('after')
    parser.add_argument('--allow', action='append', default=[])
    args = parser.parse_args(argv)
    try:
        result = compare(args.before, args.after, args.allow)
    except (OSError, ValueError) as exc:
        # Do not echo source paths or operating-system error details.
        print(json.dumps({'error': type(exc).__name__, 'status': 'comparison-incomplete'}))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result['unexpected_changes'] else 0

if __name__ == '__main__':
    sys.exit(main())
