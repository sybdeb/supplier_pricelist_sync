{
    "name": "Supplier Pricelist Sync v3.6 (Freemium - Scheduled Imports)",
    "version": "19.0.3.6.0",
    "summary": "Supplier import with manual (FREE) and scheduled (PRO) imports",
    "description": """
Direct Supplier Pricelist Import System - Freemium Model:
- Central Dashboard - Import management per supplier
- Direct Import - Inline CSV processing without data loss
- Automatic Column Mapping - Smart detection based on supplier patterns
- Template System - Save and reuse mappings per supplier
- Bulk Processing - Handle large CSV files efficiently
- Brand Mapping - Map CSV brand names to Odoo brands
- Update Logic - Refresh existing records, no duplicates

FREE Version (Manual Imports):
- Maximum 2 imports per day per user
- Maximum 2000 rows per import
- Manual CSV upload only

PRO Version (Scheduled Automation):
- Unlimited imports per day
- Unlimited file size
- Scheduled Imports - HTTP/FTP/SFTP/API/Database
- Automatic periodic imports via cron
- All PRO features visible in UI, unlocked by installing supplier_sync_pro

Contact: info@de-bruijn.email for PRO upgrade

Built for Odoo 19 Community Edition
""",
    "author": "De Bruijn Webworks in samenwerking met Nerbys E-commerce",
    "website": "https://nerbys.nl",
    "support": "info@de-bruijn.email",
    "depends": ["base", "product", "purchase", "mail", "dbw_odoo_base_v2"],
    "external_dependencies": {
        "python": ["paramiko", "requests"]  # Required for PRO scheduled imports
    },
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
        "views/product_central_dashboard_views.xml",
        "views/res_partner_views.xml",
        "views/smart_import_views.xml",
        "views/smart_import_session_views.xml",
        "views/advanced_wizard_views.xml",
        "views/mapping_save_wizard_views.xml",
        "views/wizard_action.xml",
        "views/menus.xml",
        "views/brand_mapping_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}

