#!/usr/bin/env python3
"""
Generate current-members.json from Congress.gov API
Includes leadership positions for each member
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

def fetch_url(url):
    """Fetch data from Congress.gov API with error handling"""
    try:
        req = urllib.request.Request(url)
        req.add_header('X-API-Key', API_KEY)  # Now safe - API_KEY is validated as str
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        return None
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_member_leadership(bioguideId):
    """Fetch leadership positions for a specific member"""
    url = f"{BASE_URL}/member/{bioguideId}?api_key={API_KEY}"
    data = fetch_url(url)
    if data and 'member' in data:
        return data['member'].get('leadership', [])
    return []

def get_current_members():
    """Fetch all current members of Congress"""
    # Fetch all current members (both chambers)
    url = f"{BASE_URL}/member?api_key={API_KEY}&limit=550"
    data = fetch_url(url)
    
    if not data or 'members' not in data:
        print("Error: Could not fetch member list")
        return []
    
    members = data['members'].get('member', [])
    print(f"Found {len(members)} members in initial fetch")
    
    # Filter to only current members (those with current terms)
    current_members = []
    for member in members:
        # Check if member has current terms
        terms = member.get('terms', {}).get('item', [])
        if terms:
            # Check if any term is current (endYear is null or in the future)
            current_year = datetime.now().year
            has_current_term = any(
                term.get('endYear') is None or term.get('endYear', 0) >= current_year
                for term in terms
            )
            if has_current_term:
                current_members.append(member)
    
    print(f"Filtered to {len(current_members)} current members")
    return current_members

def enrich_member_data(member):
    """Enrich member data with leadership positions"""
    bioguideId = member.get('bioguideId', '')
    
    # Fetch leadership data from individual member endpoint
    leadership = get_member_leadership(bioguideId)
    
    # Add leadership to member data
    member['leadership'] = leadership
    
    # Add metadata
    member['dataUpdatedAt'] = datetime.now().isoformat()
    
    return member

def main():
    # API key validation moved to top of script
    
    print("Fetching current Congress members...")
    members = get_current_members()
    
    if not members:
        print("Error: No members fetched")
        sys.exit(1)
    
    print("Enriching member data with leadership positions...")
    enriched_members = []
    for i, member in enumerate(members):
        print(f"  Processing {i+1}/{len(members)}: {member.get('name', 'Unknown')}")
        enriched_member = enrich_member_data(member)
        enriched_members.append(enriched_member)
        
        # Rate limiting: Congress.gov API allows 1000 requests per hour
        # Add small delay to be safe
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(members)} members processed")
    
    # Create output structure
    output_data = {
        'metadata': {
            'generatedAt': datetime.now().isoformat(),
            'source': 'Congress.gov API',
            'count': len(enriched_members)
        },
        'members': enriched_members
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Write to file
