# -*- coding: utf-8 -*-
"""
Basic tests for Supplier Pricelist Sync module
"""
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestSupplierSync(TransactionCase):
    """Test basic module functionality"""

    def setUp(self):
        super(TestSupplierSync, self).setUp()
        
        # Create test supplier
        self.supplier = self.env['res.partner'].create({
            'name': 'Test Supplier',
            'supplier_rank': 1,
            'is_company': True,
        })
        
        # Create test product
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'default_code': 'TEST001',
            'barcode': '1234567890123',
        })

    def test_module_installed(self):
        """Test that the module is installed correctly"""
        module = self.env['ir.module.module'].search([
            ('name', '=', 'product_supplier_sync'),
            ('state', '=', 'installed')
        ])
        self.assertTrue(module, "Module should be installed")

    def test_supplier_has_last_sync_field(self):
        """Test that suppliers have last_sync_date field"""
        self.assertIn('last_sync_date', self.supplier._fields)
        # In Odoo, date fields default to False, not None
        self.assertFalse(self.supplier.last_sync_date)

    def test_supplierinfo_creation(self):
        """Test creating a supplier info record"""
        supplierinfo = self.env['product.supplierinfo'].create({
            'partner_id': self.supplier.id,
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'price': 100.0,
            'min_qty': 1,
        })
        self.assertEqual(supplierinfo.price, 100.0)
        self.assertIn('last_sync_date', supplierinfo._fields)

    def test_product_reactivation(self):
        """Test that archived products can be reactivated"""
        # Archive product
        self.product.active = False
        self.assertFalse(self.product.active)
        
        # Reactivate
        self.product.active = True
        self.assertTrue(self.product.active)

    def test_import_history_model(self):
        """Test that import history model exists"""
        history = self.env['supplier.import.history'].create({
            'supplier_id': self.supplier.id,
            'filename': 'test.csv',
            'total_rows': 10,
            'state': 'completed',
        })
        self.assertEqual(history.supplier_id, self.supplier)
        self.assertEqual(history.state, 'completed')

    def test_previous_price_tracking(self):
        """Test that previous_price is saved when price changes"""
        # Create initial supplierinfo
        supplierinfo = self.env['product.supplierinfo'].create({
            'partner_id': self.supplier.id,
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'price': 100.0,
        })
        
        # Verify initial state (no previous price yet)
        self.assertEqual(supplierinfo.price, 100.0)
        self.assertEqual(supplierinfo.previous_price, 0.0)
        self.assertEqual(supplierinfo.price_change_pct, 0.0)
        
        # Update price (simulating import update)
        supplierinfo.write({
            'previous_price': supplierinfo.price,  # Save old price
            'price': 80.0,  # New price
        })
        
        # Verify previous_price was saved and change calculated
        self.assertEqual(supplierinfo.price, 80.0)
        self.assertEqual(supplierinfo.previous_price, 100.0)
        self.assertEqual(supplierinfo.price_change_pct, -20.0)  # -20% daling
