"""Copy the playable game from this repository into the website repository.

The website (github.com/Book15011/Book15011.github.io) serves a copy of poker/ without the tests, tooling,
training code or research. This mirrors the files the game needs at runtime and touches nothing else:
files that changed are copied, and files the game no longer has are removed, inside the folders below only.
It never commits. Review the result in the website checkout, then commit and push there to deploy.

Usage: python scripts/publish_site.py <path to the website checkout> [--dry-run]
"""
import argparse
import filecmp
import shutil
import sys
from pathlib import Path

RUNTIME_FILES = ['index.html', 'how-it-works.html']
RUNTIME_DIRS = ['css', 'js', 'models', 'data']

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('site', type=Path, help='path to the Book15011.github.io checkout')
parser.add_argument('--dry-run', action='store_true', help='show what would change without changing anything')
args = parser.parse_args()

src = Path(__file__).resolve().parent.parent / 'poker'
site = args.site.resolve()
dst = site / 'poker'
if not (site / 'quant.html').is_file() or not dst.is_dir():
    sys.exit(f'{site} does not look like the website checkout (expected quant.html and a poker/ folder)')

changes = []


def copy(a: Path, b: Path):
    if b.is_file() and filecmp.cmp(a, b, shallow=False):
        return
    changes.append(('update' if b.exists() else 'add', b))
    if not args.dry_run:
        b.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(a, b)


for name in RUNTIME_FILES:
    copy(src / name, dst / name)

for name in RUNTIME_DIRS:
    s, d = src / name, dst / name
    wanted = {p.relative_to(s) for p in s.rglob('*') if p.is_file()}
    for rel in sorted(wanted):
        copy(s / rel, d / rel)
    if d.is_dir():
        for p in sorted(d.rglob('*'), reverse=True):
            rel = p.relative_to(d)
            if p.is_file() and rel not in wanted:
                changes.append(('remove', p))
                if not args.dry_run:
                    p.unlink()
            elif p.is_dir() and not args.dry_run and not any(p.iterdir()):
                p.rmdir()

for kind, path in changes:
    print(f'{kind:7} {path.relative_to(site).as_posix()}')
print(f'{len(changes)} change(s){" (dry run, nothing written)" if args.dry_run else ""}')
