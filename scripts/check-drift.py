"""Compare repo examples with public consumers without changing either side."""
import argparse
import base64
import difflib
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def canonical(value):
    """Ignore JSON formatting and object key order, retaining rule order."""
    return json.dumps(value, indent=2, sort_keys=True).splitlines(keepends=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', action='append', help='Only check named repositories')
    args = parser.parse_args()
    failed = False
    for path in sorted(Path('repos').glob('*.json')):
        if args.repo and path.stem not in args.repo:
            continue
        headers = {'Accept': 'application/vnd.github+json'}
        if token := os.environ.get('GH_TOKEN'):
            headers['Authorization'] = f'Bearer {token}'
        request = Request(f'https://api.github.com/repos/tjorim/{path.stem}/contents/renovate.json', headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                remote = json.load(response)
            live = json.loads(base64.b64decode(remote['content']))
        except (HTTPError, URLError) as error:
            # A draft example for a repository that has not adopted Renovate is expected.
            if isinstance(error, HTTPError) and error.code == 404:
                print(f'{path.stem}: no accessible main config (not adopted or not accessible); skipped')
                continue
            print(f'{path.stem}: unable to check: {error}')
            failed = True
            continue
        expected = json.loads(path.read_text())
        if expected != live:
            failed = True
            print(''.join(difflib.unified_diff(canonical(expected), canonical(live), fromfile=str(path), tofile=f'{path.stem}/main')))
        else:
            print(f'{path.stem}: matches')
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
