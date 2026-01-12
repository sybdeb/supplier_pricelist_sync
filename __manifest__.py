{
    "name": "Supplier Pricelist Sync v3.5 (Hub Integration - FREE)",
    "version": "19.0.3.5.0",
    "summary": "Direct supplier pricelist import with DBW Base v2 integration (FREE: 2/day, 2000 rows)",
    "description": """
Direct Supplier Pricelist Import System - FREE Version:
- Central Dashboard - Import management per supplier
- Direct Import - Inline CSV processing without data loss
- Automatic Column Mapping - Smart detection based on supplier patterns
- Template System - Save and reuse mappings per supplier
- Bulk Processing - Handle large CSV files efficiently (v3.0: batch commits)
- Update Logic - Refresh existing records, no duplicates
- Batch Processing - 250-row commits to prevent worker timeouts (v3.0.1)

FREE Version Limitations (v19.0.3.5.0):
- Maximum 2 imports per day per user
- Maximum 2000 rows per import
- Manual imports only

PRO Version Available:
- Unlimited imports per day
- Unlimited file size
- Scheduled Imports - FTP/SFTP/API/HTTP automation
- Cron Integration - Automatic periodic imports

Contact: info@de-bruijn.email for PRO upgrade

Built for Odoo 19 Community Edition
""",
    "author": "De Bruijn Webworks in samenwerking met Nerbys E-commerce",
    "website": "https://nerbys.nl",
    "support": "info@de-bruijn.email",
    "depends": ["base", "product", "purchase", "mail", "dbw_odoo_base_v2"],
    "license": "LGPL-3",
    "category": "Purchases",
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
        "views/brand_mapping_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}

