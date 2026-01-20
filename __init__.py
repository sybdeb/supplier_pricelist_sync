from . import models
from . import wizard


def uninstall_hook(env):
    """
    Clean up all module data on uninstall to prevent foreign key constraint violations
    """
    # Delete all menu items recursively (children first, then parents)
    menus = env['ir.ui.menu'].search([('name', 'ilike', 'Supplier Import')])
    if menus:
        # Get all child menus recursively
        all_menus = menus
        for menu in menus:
            children = env['ir.ui.menu'].search([('parent_id', 'child_of', menu.id)])
            all_menus |= children
        
        # Delete from deepest level upwards
        all_menus.sorted(lambda m: -len(m.parent_path or '')).unlink()
    
    # Clean up any orphaned data
    # Import history
    env['supplier.import.history'].search([]).unlink()
    
    # Import queue
    env['supplier.import.queue'].search([]).unlink()
    
    # Scheduled imports
    env['supplier.import.schedule'].search([]).unlink()
    
    # Mapping templates
    env['supplier.mapping.template'].search([]).unlink()
    
    # Brand mappings
    env['supplier.brand.mapping'].search([]).unlink()
