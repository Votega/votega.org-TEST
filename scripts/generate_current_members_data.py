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


def is_current_member(member, year):
    terms = member.get('terms', {}).get('item', [])
    if not isinstance(terms, list):
        return False
    for term in terms:
        if term.get('chamber') not in ('House of Representatives', 'Senate'):
            continue
        start = term.get('startYear')
        end = term.get('endYear')
        if isinstance(start, int) and start <= year and (end is None or end >= year):
            return True
        else:
            print(f"Skipping {member.get('name')} ({member.get('state')}) - start: {start}, end: {end}")
    return False


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

    # Fetch the full member list and derive current members from term dates.
    while True:
        data = fetch_page(api_key, offset)
        page_members = data.get('members') or []
        members.extend(page_members)
        pagination = data.get('pagination', {})
        if not pagination.get('next'):
            break
        offset += len(page_members)

    current_year = time.gmtime().tm_year
    current_members = [m for m in members if is_current_member(m, current_year)]

    print(f'Fetched {len(members)} total members and {len(current_members)} current members from list endpoint')

    output = {
        'updatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'source': 'https://api.congress.gov/v3/member?format=json (filtered by current term dates)',
        'count': len(current_members),
        'members': current_members,
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
        f.write('\n')

    print(f'Wrote {len(current_members)} members to {output_path}')
