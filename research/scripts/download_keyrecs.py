"""Download only the licensed fixed-text release; never replace differing raw data."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
BASE='https://zenodo.org/api/records/7886743'
EXPECTED_MD5='f3c2ef3a42625f4df7183ea36d4543db'


def fetch(url):
    request=urllib.request.Request(url,headers={'User-Agent':'KeyGuard coursework reproducibility'})
    with urllib.request.urlopen(request,timeout=60) as response:return response.read()


def main():
    directory=ROOT/'data/raw/keyrecs';directory.mkdir(parents=True,exist_ok=True)
    metadata_path=directory/'metadata.json'
    metadata_bytes=metadata_path.read_bytes() if metadata_path.exists() else fetch(BASE)
    metadata=json.loads(metadata_bytes)
    assert metadata['metadata']['license']['id']=='cc-by-4.0'
    entry=next(f for f in metadata['files'] if f['key']=='fixed-text.csv')
    assert entry['checksum']=='md5:'+EXPECTED_MD5
    raw_path=directory/'fixed-text.csv'
    data=raw_path.read_bytes() if raw_path.exists() else fetch(entry['links']['self'])
    if hashlib.md5(data).hexdigest()!=EXPECTED_MD5:
        raise ValueError('Existing/downloaded raw differs from pinned version; preserve and investigate')
    if not metadata_path.exists():metadata_path.write_bytes(metadata_bytes)
    if not raw_path.exists():raw_path.write_bytes(data)
    manifest={'dataset':'KeyRecs fixed-text','version':'1.0.0','record':'https://zenodo.org/records/7886743',
              'article':'https://doi.org/10.1016/j.dib.2023.109509','license':'CC BY 4.0',
              'license_url':'https://creativecommons.org/licenses/by/4.0/',
              'attribution':'Tiago Dias, João Vitorino, Eva Maia, Orlando Sousa, Isabel Praça (2023)',
              'local_file':'data/raw/keyrecs/fixed-text.csv','raw_bytes':len(data),
              'published_md5':EXPECTED_MD5,'sha256':hashlib.sha256(data).hexdigest(),
              'metadata_sha256':hashlib.sha256(metadata_bytes).hexdigest(),
              'demographics_and_free_text_not_downloaded':True,
              'modifications':'Raw unchanged; adapter canonicalizes duplicate header positions, keeps all47 timing features. No raw redistribution.'}
    path=ROOT/'data/keyrecs_manifest.json'
    if path.exists() and json.loads(path.read_text(encoding='utf-8'))!=manifest:
        raise ValueError('Manifest differs; do not overwrite existing provenance')
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Verified cached/downloaded KeyRecs fixed-text checksum and CC BY4.0; manifest saved')


if __name__=='__main__':main()
