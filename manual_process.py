#!/usr/bin/env python3
import sys
sys.path.append('/usr/lib/python3/dist-packages')
import odoo
from odoo import api, SUPERUSER_ID

# Initialize Odoo
odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf', '-d', 'nerbys'])
odoo.service.server.start(preload=[], stop=True)

# Get environment
cr = odoo.sql_db.db_connect('nerbys').cursor()
env = api.Environment(cr, SUPERUSER_ID, {})

# Get the model
model = env['supplier.import.queue']

# Find queued imports
queue_items = model.search([('state', '=', 'queued')])
print(f"Found {len(queue_items)} queued imports")

if queue_items:
    for item in queue_items:
        print(f"Processing {item.id}")
        try:
            item.state = 'processing'
            item.history_id.state = 'running'
            cr.commit()
            item._execute_queued_import()
            item.state = 'done'
            cr.commit()
            print(f"Completed {item.id}")
        except Exception as e:
            print(f"Failed {item.id}: {e}")
            item.state = 'failed'
            item.history_id.write({
                'state': 'failed',
                'summary': f"Manual import failed: {str(e)}",
            })
            cr.commit()
else:
    print("No queued imports found")

cr.close()