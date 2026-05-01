#!/usr/bin/env python3
"""
Generate current-members.json from Congress.gov API
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime

# Configuration
API_KEY = os.environ.get('CONGRESS_API_KEY')
BASE_URL = "https://api.congress.gov/v3"
OUTPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "assets/data/current-members.json"

def fetch_url(url):
    """Fetch data from Congress.gov API with error handling"""
    try:
        # Add API key as query parameter (required by Congress.gov API)
        if 'api_key=' not in url:
            separator = '&' if '?' in url else '?'
            url = f"{url}{separator}api_key={API_KEY}"
        
        print(f"Fetching: {url[:100]}...")
        
        req = urllib.request.Request(url)
        # No header needed - API key works via query parameter
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"Error fetching {url[:100]}: {e}")
        return None

def get_member_details(bioguideId):
    """Fetch detailed member data"""
    url = f"{BASE_URL}/member/{bioguideId}?format=json"
    data = fetch_url(url)
    if data and 'member' in data:
        return data['member']
    return None

def extract_leadership(member_data):
    """Extract leadership positions"""
    leadership = member_data.get('leadership', [])
    
    # Handle both list and dict with 'item' key
    if isinstance(leadership, dict):
        leadership = leadership.get('item', [])
    
    if not isinstance(leadership, list):
        leadership = [leadership] if leadership else []
    
    # Extract current leadership positions
    current_leadership = []
    for position in leadership:
        if isinstance(position, dict):
            # Include if marked as current OR if no 'current' field (assume current)
            if position.get('current') == True or 'current' not in position:
                current_leadership.append({
                    'title': position.get('type', position.get('title', 'Unknown')),
                    'congress': position.get('congress', ''),
                    'current': position.get('current', True)
                })
    
    return current_leadership

def enrich_member_data(bioguideId, basic_member):
    """Fetch and enrich member data"""
    member_details = get_member_details(bioguideId)
    
    if not member_details:
        print(f"Warning: Could not fetch details for {bioguideId}, using basic data")
        basic_member['leadership'] = []
        basic_member['contactInfo'] = {}
        basic_member['officialWebsiteUrl'] = ''
        basic_member['birthYear'] = ''
        basic_member['dataUpdatedAt'] = datetime.now().isoformat()
        return basic_member
    
    basic_member['leadership'] = extract_leadership(member_details)
    basic_member['contactInfo'] = member_details.get('addressInformation', {})
    basic_member['officialWebsiteUrl'] = member_details.get('officialWebsiteUrl', '')
    basic_member['birthYear'] = member_details.get('birthYear', '')
    basic_member['currentMember'] = member_details.get('currentMember', False)
    basic_member['honorificName'] = member_details.get('honorificName', '')
    basic_member['firstName'] = member_details.get('firstName', '')
    basic_member['lastName'] = member_details.get('lastName', '')
    basic_member['sponsoredLegislation'] = member_details.get('sponsoredLegislation', {})
    basic_member['cosponsoredLegislation'] = member_details.get('cosponsoredLegislation', {})
    basic_member['dataUpdatedAt'] = datetime.now().isoformat()
    
    return basic_member

def get_current_members():
    """Fetch all current members of Congress"""
    url = f"{BASE_URL}/member?limit=550&format=json"
    data = fetch_url(url)
    
    if not data or 'members' not in data:
        print("Error: Could not fetch member list")
        return []
    
    members = data['members'].get('member', [])
    print(f"Found {len(members)} members in initial fetch")
    
    # Filter to only current members
    current_members = []
    for member in members:
        terms = member.get('terms', {}).get('item', [])
        if terms:
            current_year = datetime.now().year
            has_current_term = any(
                term.get('endYear') is None or term.get('endYear', 0) >= current_year
                for term in terms
            )
            if has_current_term:
                current_members.append(member)
    
    print(f"Filtered to {len(current_members)} current members")
    return current_members

def main():
    if not API_KEY:
        print("Error: CONGRESS_API_KEY environment variable not set")
        sys.exit(1)
    
    print("Fetching current Congress members...")
    members = get_current_members()
    
    if not members:
        print("Error: No members fetched")
        sys.exit(1)
    
    print("Enriching member data with leadership positions...")
    enriched_members = []
    for i, member in enumerate(members):
        bioguideId = member.get('bioguideId', '')
        print(f"  Processing {i+1}/{len(members)}: {member.get('name', 'Unknown')} ({bioguideId})")
        enriched_member = enrich_member_data(bioguideId, member)
        enriched_members.append(enriched_member)
        
        if (i + 1) % 5 == 0:
            print(f"  Progress: {i+1}/{len(members)} members processed")
    
    # Create output structure
    output_data = {
        'metadata': {
            'generatedAt': datetime.now().isoformat(),
            'source': 'Congress.gov API',
            'count': len(enriched_members),
            'apiVersion': 'v3'
        },
        'members': enriched_members
    }
    
    # Ensure output directory exists (simple approach)
    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        print(f"Directory check passed for {OUTPUT_FILE}")
    except Exception as e:
        print(f"Directory creation error: {e}")
        sys.exit(1)
    
    # Write to file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Successfully wrote {len(enriched_members)} members to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error writing file: {e}")
        sys.exit(1)
    
    # Print summary
    leadership_count = sum(1 for m in enriched_members if m.get('leadership'))
    print(f"Members with leadership positions: {leadership_count}")

if __name__ == '__main__':
    main()
