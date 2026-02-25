{
    'name': 'DBW Odoo Base',
    'version': '19.0.5.1.1',
    'category': 'Technical',
    'summary': 'Central hub for DBW modules with unified dashboard, settings, processing queue, brand management and product enrichment logging',
    'description': '''
        DBW Odoo Base Module
        ====================
        Core infrastructure for DBW modules providing:
        - Central service layer for common operations
        - Unified dashboard collecting widgets from modules
        - Centralized settings page
        - Processing queue for pipeline orchestration (Supplier → Quality → Pricing → Publish)
        - Import audit trail (history & errors)
        - Product Brand Management (core to DBW business)
        - Product Enrichment Logging (persistent tracking across module reinstalls)
        - Menu structure for all DBW applications
        - Automatic scheduled import checker (runs hourly to trigger due imports)
    ''',
    'author': 'DBW',
    'website': 'https://www.dbw.nl',
    'depends': [
        'base',
        'web',
        'product',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',  # Cron jobs for scheduled imports
        'views/menu.xml',  # Load menus first - defines menu_dbw_products needed by other views
        'views/dashboard.xml',
        'views/settings.xml',
        # 'views/processing_queue.xml',  # Temporarily disabled - view definition issue
        'views/product_brand.xml',
        # 'views/product_enrichment_log_views.xml',  # Temp disabled - deploy models first
        # 'views/product_template_enrichment_views.xml',  # Temp disabled - deploy models first
        'views/sync_log_views.xml',
    ],
    'external_dependencies': {
        'python': [],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}


