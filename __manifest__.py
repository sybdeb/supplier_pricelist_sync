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
        # "views/smart_import_session_views.xml",  # DISABLED - experimental feature causing view conflicts
        "views/supplier_mapping_template_views.xml",
        "views/product_supplierinfo_views.xml",
        "views/product_template_views.xml",
        "views/wizard_action.xml",
        "views/test_actions.xml",
        "views/supplier_native_import_views.xml",  # NEW: Native import integration
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "supplier_pricelist_sync/static/src/js/smart_import_state_manager.js",
            "supplier_pricelist_sync/static/src/js/smart_import_fixed_v1.js", 
            "supplier_pricelist_sync/static/src/js/smart_import_fixed_v2.js",
            "supplier_pricelist_sync/static/src/xml/smart_import_templates.xml",
            "supplier_pricelist_sync/static/src/xml/smart_import_fixed_templates.xml",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
