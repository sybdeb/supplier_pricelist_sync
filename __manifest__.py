{
    "name": "Supplier Pricelist Sync v1.3 (Enhanced)",
    "version": "18.0.1.3",
    "summary": "Importeer leveranciersprijslijsten via CSV met preview en partner_id",
    "description": """
Enhanced module voor het importeren van leveranciersprijslijsten:
- CSV preview met eerste 5 regels
- Automatische partner_id kolom toevoeging
- Direct import in Odoo's native wizard
- Geschikt voor Odoo 18 Community (Synology/Docker)
""",
    "author": "Nerbys",
    "website": "https://nerbys.nl",
    "license": "LGPL-3",
    "category": "Purchases",
    "depends": ["base", "product", "purchase"],
    "data": [
        "security/ir.model.access.csv",
        "views/product_supplierinfo_views.xml",
        "views/wizard_action.xml",
        "views/wizard_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
