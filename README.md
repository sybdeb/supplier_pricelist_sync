# Supplier Pricelist Sync v2.1

[![License: LGPL-3](https://img.shields.io/badge/licence-LGPL--3-blue.svg)](http://www.gnu.org/licenses/lgpl-3.0-standalone.html)
[![Odoo Version](https://img.shields.io/badge/Odoo-19.0-purple.svg)](https://www.odoo.com/)

**Automated supplier pricelist synchronization for Odoo 19 Community Edition**

## 📋 Overview

Import supplier pricelists directly into Odoo via multiple connection methods:
- **HTTP/HTTPS** - Download CSV/JSON/XML files from web servers
- **REST API** - Connect to supplier APIs with automatic JSON→CSV conversion  
- **FTP/SFTP** - Retrieve files from FTP servers
- **Database** - Direct PostgreSQL/MySQL/MSSQL queries

Features intelligent column mapping, automatic template creation, and scheduled imports with full history tracking.

## ✨ Key Features

### 🔄 Multiple Import Methods
- **HTTP/HTTPS Downloads** - Direct file downloads from URLs
- **REST API Integration** - JSON APIs with automatic CSV conversion
- **SFTP/FTP Servers** - Automated file retrieval with pattern matching
- **Database Connections** - Direct SQL queries to supplier databases

### 🎯 Smart Mapping System
- **Auto-detection** - Automatically detects CSV columns on first import
- **Template System** - Save and reuse column mappings per supplier
- **Dynamic Updates** - Auto-adds new columns when supplier adds fields
- **Flexible Mapping** - Map to product fields, supplier info, or leave unmapped

### 📊 Import Management
- **Scheduled Imports** - Configure automatic imports (hourly/daily/weekly)
- **Manual Triggers** - Run imports on-demand with "Run Import Now" button
- **Import History** - Complete audit trail with success/warning/error tracking
- **Statistics Dashboard** - Overview of all imports per supplier

### 🔐 Security & Authentication
- **API Authentication** - Support for Basic Auth, Bearer tokens, and API keys
- **SFTP Keys** - Secure file transfers with username/password
- **Database Credentials** - Encrypted connection strings

## 🚀 Installation

### Requirements
- Odoo 19.0 Community or Enterprise
- Python 3.10+
- PostgreSQL 12+

### Dependencies
The following Python packages are automatically installed:
- `paramiko` - For SFTP connections
- `psycopg2` - For PostgreSQL database imports (usually pre-installed)
- `requests` - For HTTP/API imports (pre-installed with Odoo)

### Install Steps

1. **Clone or download** this module to your Odoo addons directory:
```bash
cd /path/to/odoo/addons
git clone https://github.com/yourusername/supplier_pricelist_sync.git
```

2. **Restart Odoo** to load the new module

3. **Update Apps List** in Odoo (Settings → Apps → Update Apps List)

4. **Install Module**:
   - Go to Apps
   - Search for "Supplier Pricelist Sync"
   - Click Install

## 📖 Usage

### Quick Start: Manual Import

1. **Navigate** to Supplier Import → Direct Import
2. **Select Supplier** from dropdown
3. **Upload CSV** file
4. **Review Mappings** - System auto-detects columns
5. **Click Import** - Products are matched and updated

### Scheduled Imports Setup

1. **Navigate** to Supplier Import → Scheduled Imports
2. **Create** new scheduled import
3. **Configure** connection:
   - Select import method (HTTP/API/SFTP/Database)
   - Enter connection details (URL, credentials, etc.)
   - Set schedule type (Manual/Hourly/Daily/Weekly)
4. **Test** with "Run Import Now" button
5. **Save** - On first run, template is auto-created
6. **Map Columns** - Open template and assign Odoo fields
7. **Activate** - Toggle active switch to enable automation

### Column Mapping

#### First Import Flow
1. System downloads data and detects columns
2. Template created with all detected columns (unmapped)
3. User opens template to assign mappings
4. Future imports use saved mappings automatically

#### Required Mappings
For successful import, map at minimum:
- **Product Identifier**: Either `Barcode` (EAN) or `Internal Reference` (SKU)
- **Price**: `[Leverancier] Prijs` field

#### Optional Mappings
- **Stock**: Supplier stock quantity
- **Delivery Time**: Lead time in days
- **Product Name**: For creating new products
- **Brand**: Product brand

### Import Methods Details

#### HTTP/HTTPS
- **Use for**: Direct file downloads (CSV, JSON, XML)
- **Config**: Download URL
- **Example**: `http://supplier.com/exports/pricelist.csv`

#### REST API
- **Use for**: JSON APIs
- **Config**: API Endpoint + Authentication
- **Features**: Automatic JSON to CSV conversion
- **Auth Types**: None, Basic, Bearer Token, API Key

#### FTP/SFTP
- **Use for**: Files on FTP servers
- **Config**: Host, Port, Username, Password, Path, Filename Pattern
- **Features**: Automatically selects newest matching file
- **Example Pattern**: `pricelist_*.csv`

#### Database
- **Use for**: Direct database queries
- **Config**: DB Type, Host, Port, Database Name, Username, Password, SQL Query
- **Supported**: PostgreSQL, MySQL, MS SQL Server
- **Example Query**: `SELECT ean, sku, price, stock FROM products WHERE active = true`

## 📁 Module Structure

```
supplier_pricelist_sync/
├── models/
│   ├── dashboard.py                    # Statistics dashboard
│   ├── direct_import.py                # Manual CSV import wizard
│   ├── import_history.py               # Import audit trail
│   ├── import_schedule.py              # Scheduled imports (main logic)
│   ├── supplier_mapping_template.py    # Column mapping templates
│   ├── product_supplierinfo.py         # Supplierinfo extensions
│   ├── product_template.py             # Product template extensions
│   └── base_import_extend.py           # Prevent duplicate supplierinfo
├── wizard/
│   └── mapping_save_wizard.py          # Save mapping as template
├── views/
│   ├── dashboard_views.xml
│   ├── direct_import_views.xml
│   ├── import_history_views.xml
│   ├── import_schedule_views.xml
│   ├── supplier_mapping_template_views.xml
│   ├── product_supplierinfo_views.xml
│   ├── product_template_views.xml
│   └── menus.xml
├── security/
│   └── ir.model.access.csv
├── data/                               # Sample CSV files
│   ├── copaco_sample.csv
│   ├── generic_sample.csv
│   └── edge_case_sample.csv
└── __manifest__.py
```

## 🔧 Configuration

### Cron Jobs
Scheduled imports automatically create cron jobs when activated. These can be managed via:
- Settings → Technical → Automation → Scheduled Actions

### Access Rights
Default access rights:
- **Import Users**: Can view and run imports
- **Import Managers**: Can create and configure schedules
- Configure via Settings → Users & Companies → Groups

## 🐛 Known Issues & Limitations

- Email attachment import not yet implemented (planned for v2.2)
- XML parsing for API responses not implemented
- Product auto-creation from failed imports planned for v2.2

## 📝 Changelog

### v2.1.0 (Current - December 2025)
- ✅ Multiple import methods (HTTP, API, SFTP, Database)
- ✅ Automatic JSON to CSV conversion
- ✅ Scheduled imports with cron integration
- ✅ Template system with auto-column detection
- ✅ Import history and statistics
- ✅ Smart product matching (EAN/SKU)
- ✅ Duplicate prevention for supplierinfo

### v2.0.0 (October 2025)
- Direct Python import (bypassing Odoo's native import)
- Template-based column mapping
- Import history tracking
- Dashboard with statistics

### v1.0.0 (September 2025)
- Initial release with manual CSV import

## 👥 Credits

**Author**: Nerbys  
**Website**: https://nerbys.nl  
**Maintainer**: Sybren de Bruijn

## 📄 License

This module is licensed under LGPL-3.  
See [LICENSE](LICENSE) file for full details.

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📞 Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/supplier_pricelist_sync/issues
- Email: support@nerbys.nl
