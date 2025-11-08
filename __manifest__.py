{
    "name": "Supplier Pricelist Sync (Simplified v1)",
    "version": "18.0.1.0",
    "summary": "Importeer leveranciersprijslijsten via CSV",
    "description": """
Eenvoudige module om prijslijsten van leveranciers te importeren via een CSV-bestand.
Geschikt voor Odoo 18 Community (Synology/Docker).
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
