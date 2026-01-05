#!/usr/bin/env python3
"""Trigger queue processing for import ID"""

import xmlrpc.client
import json
from pathlib import Path

url = "http://localhost:19069"
db = "nerbys_dev"
username = "admin"
password = "admin"

# Connect
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})

if not uid:
    print("Auth failed")
    exit(1)

print(f"Authenticated as uid {uid}")

# Get models
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# Process all queued items via cron method
print("Processing queued imports...")

try:
    models.execute_kw(
        db, uid, password,
        'supplier.import.queue', 'process_queue',
        [[]]
    )
    print("SUCCESS: Queue processing triggered")
except Exception as e:
    print(f"ERROR: {e}")
