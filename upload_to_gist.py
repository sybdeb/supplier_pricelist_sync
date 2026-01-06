#!/usr/bin/env python3
"""Upload DBW_SUPPLIER_SYNC_INTEGRATION.md to GitHub Gist"""

import requests
import os

# Read the file
with open('DBW_SUPPLIER_SYNC_INTEGRATION.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Gist ID
gist_id = 'dbb189d6938811ad4a0ac1e4ab9b45fb'

# GitHub API endpoint
url = f'https://api.github.com/gists/{gist_id}'

# Prepare the payload
payload = {
    'files': {
        'SUPPLIER_SYNC_INTEGRATION.md': {
            'content': content
        }
    }
}

# GitHub token from environment (if available)
token = os.environ.get('GITHUB_TOKEN')

headers = {
    'Accept': 'application/vnd.github+json',
}

if token:
    headers['Authorization'] = f'Bearer {token}'

# Make the request
print(f"Uploading to gist {gist_id}...")
print(f"File size: {len(content)} bytes")

response = requests.patch(url, headers=headers, json=payload)

if response.status_code == 200:
    print("✅ Successfully uploaded to gist!")
    print(f"View at: https://gist.github.com/sybdeb/{gist_id}")
elif response.status_code == 401:
    print("❌ Authentication failed. You need to set GITHUB_TOKEN environment variable.")
    print("\nTo get a token:")
    print("1. Go to https://github.com/settings/tokens")
    print("2. Generate new token (classic)")
    print("3. Select 'gist' scope")
    print("4. Set environment variable: export GITHUB_TOKEN=your_token")
else:
    print(f"❌ Failed with status {response.status_code}")
    print(f"Response: {response.text}")
