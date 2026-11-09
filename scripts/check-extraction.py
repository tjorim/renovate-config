"""Check representative managers using presets from the candidate commit."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    'ha': (['home-assistant'], {'pep621', 'github-actions', 'homeassistant-manifest', 'pyenv'}, {
        '.python-version': '3.14.2\n',
        'pyproject.toml': '[project]\nname="fixture"\nversion="0.0.0"\ndependencies=["mygrid-modbus==0.1.1"]\n',
        'custom_components/fixture/manifest.json': '{"domain":"fixture","name":"Fixture","version":"0.0.0","requirements":["mygrid-modbus==0.1.1"]}',
    }),
    'python-library': (['python-library'], {'pep621', 'github-actions'}, {
        'pyproject.toml': '[project]\nname="fixture"\nversion="0.0.0"\ndependencies=["aiohttp>=3.10"]\n',
    }),
    'toolchains': (['default'], {'npm', 'nvm', 'nodenv', 'pyenv', 'devcontainer', 'dockerfile', 'regex', 'github-actions'}, {
        '.nvmrc': '24.13.0\n',
        '.node-version': '24.13.0\n',
        '.python-version': '3.14.2\n',
        'package.json': '{"name":"fixture","private":true,"packageManager":"pnpm@12.15.0","engines":{"node":"24.13.0","pnpm":">=12"}}',
        'Dockerfile.mcp': 'FROM node:24.13.0\nRUN npm install -g pnpm@12.15.0\n',
        '.devcontainer/devcontainer.json': '{"image":"mcr.microsoft.com/devcontainers/python:3.12","features":{"ghcr.io/devcontainers-extra/features/uv:1":{}}}',
    }),
    'rust-site': (['default', 'rust', 'astro'], {'cargo', 'npm', 'github-actions'}, {
        'Cargo.toml': '[package]\nname="fixture"\nversion="0.0.0"\nedition="2021"\n[dependencies]\nserde="1"\n',
        'package.json': '{"name":"fixture","private":true,"devDependencies":{"astro":"7.4.5"}}',
    }),
}


def main():
    ref = os.environ['PRESET_REF']
    for name, (presets, managers, files) in CASES.items():
        with tempfile.TemporaryDirectory(prefix='renovate-extract-') as tmp:
            root = Path(tmp)
            config = {'extends': [f'github>tjorim/renovate-config:{p}#{ref}' for p in presets]}
            (root/'renovate.json').write_text(json.dumps(config))
            files = dict(files)
            files['.github/workflows/ci.yml'] = 'name: Fixture\non: push\njobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v7\n'
            for file, content in files.items():
                target = root/file
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
            subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
            subprocess.run(['git', 'add', '.'], cwd=root, check=True)
            env = dict(os.environ, LOG_LEVEL='debug')
            result = subprocess.run(['npx', '--yes', '--package', 'renovate@' + (ROOT / 'renovate-version.txt').read_text().strip(), 'renovate', '--platform=local', '--dry-run=extract'], cwd=root, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            missing = [m for m in managers if f'Found {m} package files' not in result.stdout]
            if result.returncode or missing or 'ERROR:' in result.stdout:
                # Renovate masks credentials in its logs; show diagnostics on failures only.
                print(result.stdout)
                raise SystemExit(f'{name}: failed; missing managers: {missing}')
            print(f'{name}: extracted {", ".join(sorted(managers))}')


if __name__ == '__main__':
    main()
