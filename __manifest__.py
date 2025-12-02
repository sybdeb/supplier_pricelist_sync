{
    "name": "Supplier Pricelist Sync v2.1 (Scheduled Imports)",
    "version": "19.0.3.0",
    "summary": "Direct supplier pricelist import with automatic column mapping (Odoo 19)",
    "description": """
Direct Supplier Pricelist Import System:
- Central Dashboard - Import management per supplier
- Direct Import - Inline CSV processing without data loss
- Automatic Column Mapping - Smart detection based on supplier patterns
- Template System - Save and reuse mappings per supplier
- Bulk Processing - Handle large CSV files efficiently
- Update Logic - Refresh existing records, no duplicates
- Scheduled Imports - FTP/SFTP/API/Email automation
- Cron Integration - Automatic periodic imports

✨ Odoo 19 Optimizations:
- Enhanced editable field widgets for better UX
- Improved context preservation in wizards
- Cleaner code with reduced boilerplate

Built for Odoo 19 Community Edition
""",
    "author": "Nerbys",
    "website": "https://nerbys.nl",
    "license": "LGPL-3",
    "category": "Purchases",
    "depends": ["base", "product", "purchase", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/dashboard_views.xml",
        "views/direct_import_views.xml",
        "views/import_history_views.xml",
        "views/import_schedule_views.xml",
        "views/supplier_mapping_template_views.xml",
        "views/product_supplierinfo_views.xml",
        "views/product_template_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}

