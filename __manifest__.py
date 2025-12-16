{
    "name": "Product Supplier Sync PRO",
    "version": "19.0.1.0.0",
    "category": "Inventory/Purchase",
    "summary": "Scheduled supplier pricelist imports with HTTP/API/SFTP/Database connectors",
    "author": "De Bruijn Webworks",
    "website": "https://de-bruijn.dev",
    "support": "info@de-bruijn.email",
    "license": "OPL-1",
    "price": 199.00,
    "currency": "EUR",
    "depends": [
        "product_supplier_sync",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/import_schedule_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
