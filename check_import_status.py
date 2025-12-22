#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script om de status van lopende imports te checken
Gebruik: voer dit uit in Odoo shell of via Python met odoo environment
"""

def check_import_status(env):
    """Check status van alle lopende imports"""
    
    print("\n" + "="*80)
    print("IMPORT STATUS CHECK")
    print("="*80 + "\n")
    
    # Check import queue
    ImportQueue = env['supplier.import.queue']
    ImportHistory = env['supplier.import.history']
    
    # Zoek naar processing imports
    processing = ImportQueue.search([('state', '=', 'processing')])
    queued = ImportQueue.search([('state', '=', 'queued')])
    recent_done = ImportQueue.search([('state', '=', 'done')], limit=5, order='create_date desc')
    recent_failed = ImportQueue.search([('state', '=', 'failed')], limit=5, order='create_date desc')
    
    print(f"📊 QUEUE STATUS:")
    print(f"   - Processing: {len(processing)}")
    print(f"   - Queued: {len(queued)}")
    print(f"   - Recent done: {len(recent_done)}")
    print(f"   - Recent failed: {len(recent_failed)}")
    print()
    
    # Details van processing imports
    if processing:
        print("🔄 CURRENTLY PROCESSING:")
        for item in processing:
            history = item.history_id
            print(f"\n   Queue ID: {item.id}")
            print(f"   Supplier: {item.supplier_id.name}")
            print(f"   Filename: {item.csv_filename}")
            print(f"   Started: {history.import_date}")
            print(f"   Duration: {history.duration:.1f}s")
            print(f"   Progress:")
            print(f"      - Total rows: {history.total_rows}")
            print(f"      - Created: {history.created_count}")
            print(f"      - Updated: {history.updated_count}")
            print(f"      - Skipped: {history.skipped_count}")
            print(f"      - Errors: {history.error_count}")
            if history.summary:
                print(f"   Summary: {history.summary}")
            
            # Check of import stuck is
            from datetime import datetime, timedelta
            if history.write_date:
                age = datetime.now() - datetime.strptime(str(history.write_date), '%Y-%m-%d %H:%M:%S')
                minutes_ago = age.total_seconds() / 60
                print(f"   Last update: {minutes_ago:.1f} minutes ago")
                if minutes_ago > 10:
                    print(f"   ⚠️  WARNING: No update for {minutes_ago:.1f} minutes - might be stuck!")
    else:
        print("✅ No imports currently processing")
    
    # Details van queued imports
    if queued:
        print("\n⏳ QUEUED IMPORTS:")
        for item in queued:
            print(f"   - Queue ID: {item.id} | Supplier: {item.supplier_id.name} | File: {item.csv_filename}")
    
    # Recent completed
    if recent_done:
        print("\n✅ RECENT COMPLETED IMPORTS:")
        for item in recent_done:
            history = item.history_id
            print(f"   - {history.name}")
            print(f"     Duration: {history.duration:.1f}s | Created: {history.created_count} | Updated: {history.updated_count} | Errors: {history.error_count}")
    
    # Recent failed
    if recent_failed:
        print("\n❌ RECENT FAILED IMPORTS:")
        for item in recent_failed:
            history = item.history_id
            print(f"   - {history.name}")
            if history.summary:
                print(f"     Reason: {history.summary}")
    
    # Check import history direct (voor non-queued imports)
    running_history = ImportHistory.search([('state', '=', 'running')], order='import_date desc')
    if running_history:
        print("\n🔄 RUNNING IMPORTS (not in queue):")
        for hist in running_history:
            print(f"\n   Import ID: {hist.id}")
            print(f"   Supplier: {hist.supplier_id.name}")
            print(f"   Started: {hist.import_date}")
            print(f"   Duration: {hist.duration:.1f}s")
            print(f"   Progress: Created={hist.created_count} Updated={hist.updated_count} Errors={hist.error_count}")
    
    print("\n" + "="*80 + "\n")

# Gebruik in Odoo shell:
# python odoo-bin shell -d <database> -c <config_file>
# >>> from check_import_status import check_import_status
# >>> check_import_status(env)

if __name__ == '__main__':
    print("Dit script moet worden uitgevoerd in Odoo shell context.")
    print("Start Odoo shell en run:")
    print("  >>> from check_import_status import check_import_status")
    print("  >>> check_import_status(env)")
