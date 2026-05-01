#!/usr/bin/env python3
"""
Generate current-members.json from Congress.gov API
Fetches detailed member data including leadership positions, contact info, etc.
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

# Validate API key exists
if not API_KEY:
    print("Error: CONGRESS_API_KEY environment variable not set")
    sys.exit(1)

print(f"API Key present: {bool(API_KEY)}")
print(f"API Key length: {len(API_KEY)}")

def fetch_url(url):
    """Fetch data from Congress.gov API with error handling"""
    try:
        # Add API key as query parameter if not already present
        if 'api_key=' not in url:
            separator = '&' if '?' in url else '?'
            url = f"{url}{separator}api_key={API_KEY}"
        
        print(f"  Fetching: {url[:100]}...")  # Log URL (truncated for security)
        
        req = urllib.request.Request(url)
        # Also add as header (some endpoints accept both)
        if API_KEY is not None:
            req.add_header('X-API-Key', API_KEY)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.reason}")
        print(f"  URL: {url[:100]}")
        return None
    except urllib.error.URLError as e:
        print(f"  URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"  Error fetching {url[:100]}: {e}")
        return None

def get_member_details(bioguideId):
    """Fetch detailed member data from /member/{bioguideId} endpoint"""
    url = f"{BASE_URL}/member/{bioguideId}?format=json"
    data = fetch_url(url)
    if data and 'member' in data:
        return data['member']
    return None

def extract_leadership(member_data):
    """Extract leadership positions from member data"""
    leadership = member_data.get('leadership', [])
    
    # Handle both list and dict with 'item' key (API inconsistency)
    if isinstance(leadership, dict):
        leadership = leadership.get('item', [])
    
    # Ensure it's a list
    if not isinstance(leadership, list):
        leadership = [leadership] if leadership else []
    
    # Extract current leadership positions only
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

def extract_contact_info(member_data):
    """Extract contact information from member data"""
    address_info = member_data.get('addressInformation', {})
    return {
        'officeAddress': address_info.get('officeAddress', ''),
        'city': address_info.get('city', ''),
        'state': address_info.get('district', ''),  # DC is stored as 'district'
        'zipCode': address_info.get('zipCode', ''),
        'phoneNumber': address_info.get('phoneNumber', '')
    }

def extract_party(member_data):
    """Extract current party affiliation"""
    party_history = member_data.get('partyHistory', [])
    
    # Handle both list and dict with 'item' key
    if isinstance(party_history, dict):
        party_history = party_history.get('item', [])
    
    if not isinstance(party_history, list):
        party_history = [party_history] if party_history else []
    
    # Get the most recent party
    if party_history:
        sorted_parties = sorted(party_history, key=lambda x: x.get('startYear', 0), reverse=True)
        return {
            'partyName': sorted_parties[0].get('partyName', 'Unknown'),
            'partyAbbreviation': sorted_parties[0].get('partyAbbreviation', '')
        }
    
    return {'partyName': 'Unknown', 'partyAbbreviation': ''}

def enrich_member_data(bioguideId, basic_member):
    """Fetch and enrich member data with detailed information"""
    member_details = get_member_details(bioguideId)
    
    if not member_details:
        print(f"    Warning: Could not fetch details for {bioguideId}, using basic data")
        basic_member['leadership'] = []
        basic_member['contactInfo'] = {}
        basic_member['officialWebsiteUrl'] = ''
        basic_member['birthYear'] = ''
        basic_member['dataUpdatedAt'] = datetime.now().isoformat()
        return basic_member
    
    basic_member['leadership'] = extract_leadership(member_details)
    basic_member['contactInfo'] = extract_contact_info(member_details)
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
    print("Fetching current Congress members...")
    members = get_current_members()
    
    if not members:
        print("Error: No members fetched")
        sys.exit(1)
    
    print("Enriching member data with detailed information...")
    enriched_members = []
    for i, member in enumerate(members):
        bioguideId = member.get('bioguideId', '')
        print(f"  Processing {i+1}/{len(members)}: {member.get('name', 'Unknown')} ({bioguideId})")
        enriched_member = enrich_member_data(bioguideId, member)
        enriched_members.append(enriched_member)
        
        # Rate limiting: Congress.gov API allows 1000 requests per hour
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
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Write to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully wrote {len(enriched_members)} members to {OUTPUT_FILE}")
    
    # Print summary
    leadership_count = sum(1 for m in enriched_members if m.get('leadership'))
    contact_count = sum(1 for m in enriched_members if m.get('contactInfo', {}).get('phoneNumber'))
    print(f"Members with leadership positions: {leadership_count}")
    print(f"Members with contact info: {contact_count}")

if __name__ == '__main__':
    main()
