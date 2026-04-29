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


def fetch_member_details(api_key, bioguide_id):
    """Fetch full member details including district."""
    query = urllib.parse.urlencode({
        'format': 'json',
        'api_key': api_key,
    })
    url = f'https://api.congress.gov/v3/member/{bioguide_id}?{query}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        if resp.status != 200:
            raise RuntimeError(f'HTTP {resp.status}')
        return json.load(resp).get('member')


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

    # Fetch all current members from the list endpoint
    while True:
        data = fetch_page(api_key, offset)
        page_members = data.get('members') or []
        members.extend(page_members)
        pagination = data.get('pagination', {})
        if not pagination.get('next'):
            break
        offset += len(page_members)

    print(f'Fetched {len(members)} current members from list endpoint')
    
    # Enrich each member with full details including district
    enriched_members = []
    for i, member in enumerate(members):
        try:
            print(f'Fetching details for {i+1}/{len(members)}: {member.get("name")} ({member.get("bioguideId")})')
            full_details = fetch_member_details(api_key, member['bioguideId'])
            if full_details:
                # Extract the fields we need
                enriched = {
                    'bioguideId': full_details.get('bioguideId'),
                    'name': full_details.get('name'),
                    'partyName': full_details.get('partyHistory', [{}])[0].get('partyName') if full_details.get('partyHistory') else 'Unknown',
                    'state': full_details.get('state'),
                    'district': full_details.get('district'),  # This is the key field!
                    'depiction': full_details.get('depiction'),
                    'terms': full_details.get('terms'),
                }
                enriched_members.append(enriched)
            time.sleep(0.1)  # Small delay to avoid rate limiting
        except Exception as e:
            print(f'  Error fetching details: {e}')
            # Fall back to list endpoint data if detail fetch fails
            enriched_members.append(member)

    output = {
        'updatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'source': 'https://api.congress.gov/v3/member?currentMember=true&format=json (enriched with district via /member/{bioguideId})',
        'count': len(enriched_members),
        'members': enriched_members,
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
        f.write('\n')
    
    print(f'Wrote {len(enriched_members)} members to {output_path}')

    print(f'Wrote {output_path} with {len(members)} members')
