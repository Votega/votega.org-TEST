#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.parse
import urllib.request


def fetch_page(api_key, offset=0):
    query = urllib.parse.urlencode({
        'format': 'json',
        'limit': '250',
        'currentMember': 'true',
        'api_key': api_key,
        'offset': str(offset),
    })
    url = f'https://api.congress.gov/v3/member?{query}'
    print('Fetching', url)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        if resp.status != 200:
            raise RuntimeError(f'HTTP {resp.status}')
        return json.load(resp)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python scripts/generate_current_members_data.py <output-file>')
        sys.exit(1)

    output_path = sys.argv[1]
    api_key = os.environ.get('CONGRESS_API_KEY')
    if not api_key:
        raise RuntimeError('CONGRESS_API_KEY environment variable is required')

    members = []
    offset = 0

    while True:
        data = fetch_page(api_key, offset)
        page_members = data.get('members') or []
        members.extend(page_members)
        pagination = data.get('pagination', {})
        if not pagination.get('next'):
            break
        offset += len(page_members)

    output = {
        'updatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'source': 'https://api.congress.gov/v3/member?currentMember=true&format=json',
        'count': len(members),
        'members': members,
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
        f.write('\n')

    print(f'Wrote {output_path} with {len(members)} members')
