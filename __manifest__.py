{
    "name": "Supplier Pricelist Sync v1.4 (Dashboard + Smart Mapping)",
    "version": "18.0.1.4",
    "summary": "Advanced supplier pricelist import with dashboard and per-supplier column mapping",
    "description": """
Advanced Supplier Pricelist Import System:
- Central Dashboard - Import management and statistics
- Smart Column Mapping - Per-supplier automatic field matching
- Import History Tracking - Full audit trail with statistics  
- Odoo Native Integration - Extends base_import.mapping system
- Future Ready - Framework for cron/API automation (v1.5)

Built for Odoo 18 Community Edition
""",
    "author": "Nerbys",
    "website": "https://nerbys.nl",
    "license": "LGPL-3",
    "category": "Purchases",
    "depends": ["base", "product", "purchase", "base_import"],
    "data": [
        "security/ir.model.access.csv",
        "views/dashboard_views.xml",
        "views/smart_import_views.xml",
        "views/smart_import_session_views.xml",  # ENABLED: Fixed tree->list and menu parent reference
        "views/supplier_mapping_template_views.xml",
        "views/product_supplierinfo_views.xml",
        "views/product_template_views.xml",
        "views/wizard_action.xml",
        "views/menus.xml",
    ],
    # Assets removed - using server-side approach instead of JavaScript
    "installable": True,
    "application": True,
    "auto_install": False,
}
