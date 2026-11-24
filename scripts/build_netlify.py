"""Restore a pinned, verified Release snapshot before building. Never publishes."""
from pathlib import Path
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

from restore_webdata import sha

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'Favioleiva/BoliviaSatellites'


def release_tag(value):
    if not value or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', value) or value.lower() == 'latest':
        raise ValueError(
            'C05_RELEASE_REQUIRED: Configure BOLIVIA_DATA_RELEASE_TAG with an explicit '
            'published Release tag containing the ZIPs in the download manifest. '
            'Configura una Release versionada con sus paquetes; subir solo el codigo no incluye los datos.'
        )
    return value


def validate_assets(release, expected, base):
    if release.get('draft') or not release.get('published_at'):
        raise ValueError('C05_RELEASE_NOT_PUBLISHED: data must be in a published Release')
    assets = {x['name']: x for x in release.get('assets', [])}
    for item in expected:
        asset = assets.get(item['name'])
        if not asset or asset.get('state') != 'uploaded' or asset.get('size') != item['bytes']:
            raise ValueError('C05_RELEASE_ASSET_MISSING_OR_WRONG_SIZE: ' + item['name'])
        if asset.get('browser_download_url') != base + '/' + urllib.parse.quote(item['name']):
            raise ValueError('C05_RELEASE_ASSET_WRONG_URL: ' + item['name'])
        digest = asset.get('digest')
        if digest and digest != 'sha256:' + item['sha256']:
            raise ValueError('C05_RELEASE_ASSET_WRONG_HASH: ' + item['name'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-tag', default=os.environ.get('BOLIVIA_DATA_RELEASE_TAG'))
    parser.add_argument('--packages', type=Path, help='Offline QA only: verify local packages; no remote checks or downloads')
    args = parser.parse_args()
    tag = release_tag(args.release_tag)
    base = 'https://github.com/' + REPOSITORY + '/releases/download/' + urllib.parse.quote(tag)
    manifest = json.loads((ROOT / 'public/downloads/download_manifest.json').read_text(encoding='utf-8'))
    if args.packages:
        for item in manifest['files']:
            path = args.packages / item['name']
            if not path.is_file() or path.stat().st_size != item['bytes'] or sha(path) != item['sha256']:
                raise ValueError('C05_LOCAL_ASSET_MISSING_OR_WRONG_HASH: ' + item['name'])
        print('C05_LOCAL_QA_ONLY: local asset hashes verified; remote Release not checked.', flush=True)
        restore_args = ['--packages', str(args.packages.resolve())]
    else:
        request = urllib.request.Request(
            'https://api.github.com/repos/' + REPOSITORY + '/releases/tags/' + urllib.parse.quote(tag),
            headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'BoliviaSatellites-build'},
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                release = json.load(response)
        except urllib.error.HTTPError as error:
            raise ValueError('C05_RELEASE_UNAVAILABLE: HTTP ' + str(error.code) + '; publish the selected versioned assets before retrying Netlify.') from error
        if release.get('tag_name') != tag:
            raise ValueError('C05_RELEASE_WRONG_TAG')
        validate_assets(release, manifest['files'], base)
        restore_args = ['--release-base-url', base]
    subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/restore_webdata.py'), *restore_args], cwd=ROOT, check=True)
    # Only dist receives Release links. Tracked source manifests retain local URLs.
    env = dict(os.environ, BOLIVIA_RELEASE_BASE_URL=base)
    result = subprocess.run(['node', str(ROOT / 'scripts/build.mjs')], cwd=ROOT, env=env)
    if result.returncode:
        print('C05_BUILD_NOT_DEPLOYABLE: restoration succeeded; the build still failed. '
              'A size-budget failure must be resolved separately; do not bypass it.', file=sys.stderr)
    return result.returncode


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
