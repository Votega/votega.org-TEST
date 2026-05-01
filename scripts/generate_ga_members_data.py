#!/usr/bin/env python3
"""
Generate ga-members.json from Open States API (Georgia General Assembly).
Requires OPENSTATES_API_KEY environment variable.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime

API_KEY = os.environ.get('OPENSTATES_API_KEY')
BASE_URL = "https://v3.openstates.org"
OUTPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "assets/data/ga-members.json"


def fetch_url(url):
    try:
        safe_url = url if not API_KEY else url  # key is in header, not URL
        print(f"Fetching: {url[:120]}...")
        req = urllib.request.Request(url, headers={
            'X-API-Key': API_KEY,
            'Accept': 'application/json',
            'User-Agent': 'votega.org/1.0',
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"Error fetching: {e}")
        return None


def get_all_members():
    all_members = []
    page = 1
    per_page = 100

    while True:
        url = (
            f"{BASE_URL}/people"
            f"?jurisdiction=ga"
            f"&page={page}"
            f"&per_page={per_page}"
            f"&include=links"
            f"&include=contact_details"
        )
        data = fetch_url(url)

        if not data or 'results' not in data:
            print("Error: Could not fetch member list")
            break

        results = data['results']
        all_members.extend(results)

        pagination = data.get('pagination', {})
        max_page = pagination.get('max_page', 1)
        print(f"  Page {page}/{max_page}: {len(results)} members (total: {len(all_members)})")

        if page >= max_page:
            break
        page += 1

    return all_members


def normalize_member(raw):
    role = raw.get('current_role') or {}
    org = role.get('org_classification', '')

    if org == 'upper':
        chamber = 'Senate'
    elif org == 'lower':
        chamber = 'House of Representatives'
    else:
        chamber = org

    contacts = raw.get('contact_details', [])
    phone   = next((c['value'] for c in contacts if c.get('type') == 'voice'),   '')
    address = next((c['value'] for c in contacts if c.get('type') == 'address'), '')
    email   = next((c['value'] for c in contacts if c.get('type') == 'email'),   '')

    links   = raw.get('links', [])
    website = links[0]['url'] if links else ''

    birth_date = raw.get('birth_date', '') or ''
    birth_year = int(birth_date[:4]) if len(birth_date) >= 4 else None

    district_str = role.get('district', '')
    try:
        district = int(district_str)
    except (ValueError, TypeError):
        district = district_str

    return {
        'id':               raw.get('id', ''),
        'name':             raw.get('name', ''),
        'firstName':        raw.get('given_name', ''),
        'lastName':         raw.get('family_name', ''),
        'party':            raw.get('party', ''),
        'chamber':          chamber,
        'district':         district,
        'title':            role.get('title', ''),
        'imageUrl':         raw.get('image') or '',
        'phone':            phone,
        'address':          address,
        'email':            email,
        'officialWebsiteUrl': website,
        'birthDate':        birth_date,
        'birthYear':        birth_year,
    }


def main():
    if not API_KEY:
        print("Error: OPENSTATES_API_KEY environment variable not set")
        sys.exit(1)

    print("Fetching Georgia General Assembly members from Open States API...")
    raw_members = get_all_members()

    if not raw_members:
        print("Error: No members fetched")
        sys.exit(1)

    print(f"Normalizing {len(raw_members)} members...")
    members = [normalize_member(m) for m in raw_members]

    senate = [m for m in members if m['chamber'] == 'Senate']
    house  = [m for m in members if m['chamber'] == 'House of Representatives']
    print(f"  Senate: {len(senate)}  |  House: {len(house)}  |  Total: {len(members)}")

    output_data = {
        'metadata': {
            'generatedAt': datetime.now().isoformat(),
            'source':      'Open States API',
            'jurisdiction': 'Georgia',
            'count':       len(members),
        },
        'members': members,
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Successfully wrote {len(members)} GA members to {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
