{
    "name": "Supplier Pricelist Sync v3.0 (Bulk Import Optimization)",
    "version": "19.0.3.1.3",
    "summary": "Direct supplier pricelist import with automatic column mapping",
    "description": """
Direct Supplier Pricelist Import System:
- Central Dashboard - Import management per supplier
- Direct Import - Inline CSV processing without data loss
- Automatic Column Mapping - Smart detection based on supplier patterns
- Template System - Save and reuse mappings per supplier
- Bulk Processing - Handle large CSV files efficiently (NEW v3.0: 15x faster)
- Update Logic - Refresh existing records, no duplicates
- Scheduled Imports - FTP/SFTP/API/Email automation (v2.1)
- Cron Integration - Automatic periodic imports (v2.1)

Built for Odoo 19 Community Edition
""",
    "author": "De Bruijn Webworks",
    "website": "https://nerbys.nl",
    "license": "LGPL-3",
    "category": "Purchases",
    "depends": ["base", "product", "purchase", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/import_queue_cron.xml",
        "views/dashboard_views.xml",
        "views/direct_import_views.xml",
        "views/import_history_views.xml",
        "views/import_schedule_views.xml",
        "views/import_queue_views.xml",
        "views/supplier_mapping_template_views.xml",
        "views/product_supplierinfo_views.xml",
        "views/product_template_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}

