from . import models
from . import tools


def post_init_hook(env):
    """
    Hook called after module installation.
    Setup initial configuration and cron jobs.
    """
    
    # Setup cron job for processing queue
    # In Odoo 19: use 'code' instead of model_name/method
    cron = env['ir.cron'].search([
        ('name', '=', 'DBW Processing Queue Processor')
    ])
    
    if not cron:
        env['ir.cron'].create({
            'name': 'DBW Processing Queue Processor',
            'code': "model.cron_process_queue()",
            'model_id': env['ir.model']._get('dbw.processing.queue').id,
            'interval_number': 5,
            'interval_type': 'minutes',
            'active': True,
        })


def uninstall_hook(env):
    """
    Hook called after module uninstallation.
    Cleanup resources if needed.
    """
    # Processing queue items stay (for history)
    # Dashboard widgets are unregistered by modules
    pass
