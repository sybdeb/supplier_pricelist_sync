{
    "name": "Supplier Pricelist Sync v2.0 (Direct Import)",
    "version": "18.0.2.0",
    "summary": "Direct supplier pricelist import with automatic column mapping",
    "description": """
Direct Supplier Pricelist Import System:
- Central Dashboard - Import management per supplier
- Direct Import - Inline CSV processing without data loss
- Automatic Column Mapping - Smart detection based on supplier patterns
- Template System - Save and reuse mappings per supplier
- Bulk Processing - Handle large CSV files efficiently
- Update Logic - Refresh existing records, no duplicates
- Cron/API Ready - Programmatic import support

Built for Odoo 18 Community Edition
""",
    "author": "Nerbys",
    "website": "https://nerbys.nl",
    "license": "LGPL-3",
    "category": "Purchases",
    "depends": ["base", "product", "purchase"],
    "data": [
        "security/ir.model.access.csv",
        "views/dashboard_views.xml",
        "views/direct_import_views.xml",
        "views/import_history_views.xml",
        "views/supplier_mapping_template_views.xml",
        "views/product_supplierinfo_views.xml",
        "views/product_template_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}

