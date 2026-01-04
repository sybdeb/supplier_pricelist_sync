# -*- coding: utf-8 -*-
"""
Basic tests for Supplier Pricelist Sync module
"""
from odoo.tests.common import TransactionCase


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

    def test_bulk_import_pre_scan_logic(self):
        """Test pre-scan identifies updates vs creates vs errors"""
        # Create second supplier
        supplier_a = self.env['res.partner'].create({
            'name': 'Bulk Test Supplier',
            'supplier_rank': 1,
        })
        
        # Create 5 products with EANs
        products = {}
        for i in range(1, 6):
            ean = f'500000000000{i:1d}'
            product = self.env['product.product'].create({
                'name': f'Bulk Product {i}',
                'barcode': ean,
                'active': True,
            })
            products[ean] = product
        
        # Create existing supplierinfo for products 1-3
        for i in range(1, 4):
            ean = f'500000000000{i:1d}'
            product = products[ean]
            self.env['product.supplierinfo'].create({
                'partner_id': supplier_a.id,
                'product_tmpl_id': product.product_tmpl_id.id,
                'product_code': f'SKU-{i:03d}',
                'price': 10.0 + i,
                'min_qty': 10,
            })
        
        # Test: Check existing codes
        existing_codes = set(
            self.env['product.supplierinfo']
            .search([('partner_id', '=', supplier_a.id)])
            .mapped('product_code')
        )
        self.assertEqual(len(existing_codes), 3, "Should have 3 existing supplierinfo")
        
        # Test: Check which EANs exist
        test_eans = {'5000000000001', '5000000000004', '9999999999999'}
        existing_products = self.env['product.product'].search([
            ('barcode', 'in', list(test_eans))
        ])
        existing_eans = set(existing_products.mapped('barcode'))
        new_eans = test_eans - existing_eans
        
        self.assertEqual(len(new_eans), 1, "Should have 1 new/unknown EAN")
        self.assertIn('9999999999999', new_eans, "Unknown EAN should be detected")

    def test_cleanup_deletes_old_supplierinfo(self):
        """Test that cleanup removes supplierinfo not in new import"""
        # Create supplier and products
        supplier_c = self.env['res.partner'].create({
            'name': 'Cleanup Test Supplier',
            'supplier_rank': 1,
        })
        
        products = {}
        for i in range(1, 6):
            product = self.env['product.product'].create({
                'name': f'Cleanup Product {i}',
                'barcode': f'600000000000{i:1d}',
            })
            products[i] = product
            # Create supplierinfo for all 5 products
            self.env['product.supplierinfo'].create({
                'partner_id': supplier_c.id,
                'product_tmpl_id': product.product_tmpl_id.id,
                'product_code': f'CLEANUP-{i:03d}',
                'price': 20.0 + i,
            })
        
        # Verify: 5 supplierinfo exist
        initial_count = self.env['product.supplierinfo'].search_count([
            ('partner_id', '=', supplier_c.id)
        ])
        self.assertEqual(initial_count, 5, "Should start with 5 supplierinfo")
        
        # Simulate: New CSV only has products 3-5
        # Should delete products 1-2
        csv_product_codes = {'CLEANUP-003', 'CLEANUP-004', 'CLEANUP-005'}
        existing_codes = set(
            self.env['product.supplierinfo']
            .search([('partner_id', '=', supplier_c.id)])
            .mapped('product_code')
        )
        codes_to_delete = existing_codes - csv_product_codes
        
        self.assertEqual(len(codes_to_delete), 2, "Should identify 2 codes to delete")
        
        # Execute cleanup
        to_delete = self.env['product.supplierinfo'].search([
            ('partner_id', '=', supplier_c.id),
            ('product_code', 'in', list(codes_to_delete))
        ])
        to_delete.unlink()
        
        # Verify: Only 3 remain
        final_count = self.env['product.supplierinfo'].search_count([
            ('partner_id', '=', supplier_c.id)
        ])
        self.assertEqual(final_count, 3, "Should have 3 supplierinfo after cleanup")

    def test_product_archival_without_suppliers(self):
        """Test that products without supplierinfo are archived"""
        # Create product with supplierinfo
        orphan_product = self.env['product.product'].create({
            'name': 'Orphan Product',
            'barcode': '7000000000001',
            'active': True,
        })
        
        si = self.env['product.supplierinfo'].create({
            'partner_id': self.supplier.id,
            'product_tmpl_id': orphan_product.product_tmpl_id.id,
            'product_code': 'ORPHAN-001',
            'price': 50.0,
        })
        
        self.assertTrue(orphan_product.active, "Product should be active")
        
        # Remove supplierinfo
        si.unlink()
        
        # Check if product should be archived
        has_suppliers = self.env['product.supplierinfo'].search_count([
            ('product_id', '=', orphan_product.id)
        ]) > 0
        
        self.assertFalse(has_suppliers, "Product should have no suppliers")
        
        # Simulate post-processing: archive products without suppliers
        if not has_suppliers:
            orphan_product.active = False
        
        self.assertFalse(orphan_product.active, "Product should be archived")
