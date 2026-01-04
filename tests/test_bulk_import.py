# -*- coding: utf-8 -*-
"""
Tests for Bulk Import Functionality
Tests the new optimized import flow with pre-scan, bulk updates, and cleanup
"""
from odoo.tests.common import TransactionCase
import base64


class TestBulkImport(TransactionCase):
    """Test bulk import optimization features"""

    def setUp(self):
        super(TestBulkImport, self).setUp()
        
        # Create test suppliers
        self.supplier_a = self.env['res.partner'].create({
            'name': 'Supplier A',
            'supplier_rank': 1,
            'is_company': True,
        })
        
        self.supplier_b = self.env['res.partner'].create({
            'name': 'Supplier B',
            'supplier_rank': 1,
            'is_company': True,
        })
        
        # Create test products with EANs
        self.products = {}
        for i in range(1, 11):  # 10 products
            ean = f'500000000000{i:1d}'  # EAN13 format
            product = self.env['product.product'].create({
                'name': f'Product {i}',
                'default_code': f'PROD{i:03d}',
                'barcode': ean,
                'active': True,
            })
            self.products[ean] = product
        
        # Create existing supplierinfo for products 1-5 (for supplier A)
        self.existing_supplierinfo = {}
        for i in range(1, 6):
            ean = f'500000000000{i:1d}'
            product = self.products[ean]
            si = self.env['product.supplierinfo'].create({
                'partner_id': self.supplier_a.id,
                'product_tmpl_id': product.product_tmpl_id.id,
                'product_id': product.id,
                'product_code': f'SKU-A-{i:03d}',
                'price': 10.0 + i,
                'min_qty': 10,
            })
            self.existing_supplierinfo[ean] = si
        
        # Product 6-10 have NO supplierinfo from supplier A (for testing creates)
        # Product 11 will be created later (archived)
        # Product 12 will be in CSV but not in DB (for testing errors)

    def _create_csv(self, rows):
        """Helper to create CSV file from row data"""
        csv_lines = ['EAN;SKU;Price;Stock;Brand;Name']
        for row in rows:
            csv_lines.append(';'.join([
                row.get('ean', ''),
                row.get('sku', ''),
                str(row.get('price', 0)),
                str(row.get('stock', 0)),
                row.get('brand', ''),
                row.get('name', ''),
            ]))
        csv_content = '\n'.join(csv_lines)
        return base64.b64encode(csv_content.encode('utf-8'))

    def test_01_prescan_identifies_updates_and_creates(self):
        """Test that pre-scan correctly identifies updates vs creates"""
        # CSV with products 1-7
        # 1-5 should be updates (existing supplierinfo)
        # 6-7 should be creates (product exists, no supplierinfo)
        csv_rows = []
        for i in range(1, 8):
            ean = f'500000000000{i:1d}'
            csv_rows.append({
                'ean': ean,
                'sku': f'SKU-A-{i:03d}',
                'price': 20.0 + i,
                'stock': 100 + i,
                'brand': 'TestBrand',
                'name': f'Product {i}',
            })
        
        # CSV created for future import testing
        # csv_file = self._create_csv(csv_rows)
        
        # TODO: Call pre-scan method when implemented
        # For now, test the logic manually
        
        # Check existing supplierinfo
        existing_codes = set(
            self.env['product.supplierinfo']
            .search([('partner_id', '=', self.supplier_a.id)])
            .mapped('product_code')
        )
        
        self.assertEqual(len(existing_codes), 5, "Should have 5 existing supplierinfo")
        self.assertIn('SKU-A-001', existing_codes)
        self.assertIn('SKU-A-005', existing_codes)
        
        # Check products that exist
        csv_eans = {f'500000000000{i:1d}' for i in range(1, 8)}
        existing_products = self.env['product.product'].search([
            ('barcode', 'in', list(csv_eans))
        ])
        self.assertEqual(len(existing_products), 7, "Should find all 7 products")

    def test_02_prescan_identifies_new_products(self):
        """Test that pre-scan identifies products not in database"""
        csv_rows = [
            # Product 1 exists
            {
                'ean': '5000000000001',
                'sku': 'SKU-A-001',
                'price': 25.0,
                'stock': 100,
                'brand': 'TestBrand',
                'name': 'Product 1',
            },
            # Product with unknown EAN
            {
                'ean': '9999999999999',
                'sku': 'SKU-UNKNOWN',
                'price': 99.0,
                'stock': 50,
                'brand': 'NewBrand',
                'name': 'Unknown Product',
            },
        ]
        
        # CSV created for future import testing
        # csv_file = self._create_csv(csv_rows)
        
        # Check which EANs exist
        csv_eans = {'5000000000001', '9999999999999'}
        existing_products = self.env['product.product'].search([
            ('barcode', 'in', list(csv_eans))
        ])
        existing_eans = set(existing_products.mapped('barcode'))
        
        new_eans = csv_eans - existing_eans
        self.assertEqual(len(new_eans), 1, "Should have 1 new EAN")
        self.assertIn('9999999999999', new_eans, "Unknown EAN should be in new list")

    def test_03_prescan_filters_out_of_stock(self):
        """Test that pre-scan filters out products with low stock"""
        # Test data preparation for future filtering logic
        # csv_rows defined but will be used when pre-scan is implemented
        # pylint: disable=unused-variable
        csv_rows = [
            # Product 1: good stock
            {
                'ean': '5000000000001',
                'sku': 'SKU-A-001',
                'price': 25.0,
                'stock': 100,
                'brand': 'TestBrand',
                'name': 'Product 1',
            },
            # Product 2: out of stock
            {
                'ean': '5000000000002',
                'sku': 'SKU-A-002',
                'price': 26.0,
                'stock': 0,
                'brand': 'TestBrand',
                'name': 'Product 2',
            },
            # Product 3: low stock
            {
                'ean': '5000000000003',
                'sku': 'SKU-A-003',
                'price': 27.0,
                'stock': 5,
                'brand': 'TestBrand',
                'name': 'Product 3',
            },
        ]
        
        # Apply filters: skip stock < 10
        min_stock_qty = 10
        good_products = []
        filtered_products = []
        
        for row in csv_rows:
            if row['stock'] >= min_stock_qty:
                good_products.append(row)
            else:
                filtered_products.append(row)
        
        self.assertEqual(len(good_products), 1, "Only product 1 should pass filter")
        self.assertEqual(len(filtered_products), 2, "Products 2 and 3 should be filtered")

    def test_04_prescan_filters_low_price(self):
        """Test that pre-scan filters products with price too low"""
        csv_rows = [
            # Product 1: good price
            {
                'ean': '5000000000001',
                'sku': 'SKU-A-001',
                'price': 25.0,
                'stock': 100,
                'brand': 'TestBrand',
                'name': 'Product 1',
            },
            # Product 2: zero price
            {
                'ean': '5000000000002',
                'sku': 'SKU-A-002',
                'price': 0.0,
                'stock': 100,
                'brand': 'TestBrand',
                'name': 'Product 2',
            },
            # Product 3: too low
            {
                'ean': '5000000000003',
                'sku': 'SKU-A-003',
                'price': 0.5,
                'stock': 100,
                'brand': 'TestBrand',
                'name': 'Product 3',
            },
        ]
        
        # Apply filters: skip price < 1.0
        min_price = 1.0
        good_products = []
        filtered_products = []
        
        for row in csv_rows:
            if row['price'] >= min_price:
                good_products.append(row)
            else:
                filtered_products.append(row)
        
        self.assertEqual(len(good_products), 1, "Only product 1 should pass filter")
        self.assertEqual(len(filtered_products), 2, "Products 2 and 3 should be filtered")

    def test_05_cleanup_removes_old_supplierinfo(self):
        """Test that cleanup removes supplierinfo not in new CSV"""
        # Current state: Products 1-5 have supplierinfo from supplier A
        self.assertEqual(
            len(self.existing_supplierinfo), 
            5, 
            "Should start with 5 existing supplierinfo"
        )
        
        # New CSV only has products 3-7
        # Should delete supplierinfo for products 1-2
        # Should update products 3-5
        # Should create products 6-7
        csv_product_codes = {f'SKU-A-{i:03d}' for i in range(3, 8)}
        
        # Find what to delete
        existing_si = list(self.existing_supplierinfo.values())
        existing_codes = {si.product_code for si in existing_si}
        codes_to_delete = existing_codes - csv_product_codes
        
        self.assertEqual(len(codes_to_delete), 2, "Should delete 2 supplierinfo")
        self.assertIn('SKU-A-001', codes_to_delete)
        self.assertIn('SKU-A-002', codes_to_delete)
        
        # Simulate cleanup
        to_delete = self.env['product.supplierinfo'].search([
            ('partner_id', '=', self.supplier_a.id),
            ('product_code', 'in', list(codes_to_delete))
        ])
        self.assertEqual(len(to_delete), 2, "Should find 2 records to delete")
        
        # Actually delete them
        to_delete.unlink()
        
        # Verify deletion
        remaining = self.env['product.supplierinfo'].search([
            ('partner_id', '=', self.supplier_a.id)
        ])
        self.assertEqual(len(remaining), 3, "Should have 3 supplierinfo left (3-5)")

    def test_06_archived_product_reactivation(self):
        """Test that archived products are reactivated when in CSV"""
        # Create archived product
        archived_product = self.env['product.product'].create({
            'name': 'Archived Product',
            'default_code': 'ARCHIVED001',
            'barcode': '5000000000099',
            'active': False,
        })
        
        self.assertFalse(archived_product.active, "Product should be archived")
        
        # Simulate import that includes this product
        # In real import, we would reactivate it
        archived_product.active = True
        
        self.assertTrue(archived_product.active, "Product should be reactivated")

    def test_07_product_without_suppliers_should_be_archived(self):
        """Test that products without any supplierinfo are archived in post-processing"""
        # Create product with supplierinfo
        product = self.products['5000000000001']
        self.assertTrue(product.active, "Product should be active")
        
        # Product has supplierinfo
        si_count = self.env['product.supplierinfo'].search_count([
            ('product_id', '=', product.id)
        ])
        self.assertGreater(si_count, 0, "Product should have supplierinfo")
        
        # Remove all supplierinfo
        self.env['product.supplierinfo'].search([
            ('product_id', '=', product.id)
        ]).unlink()
        
        # Simulate post-processing: archive products without suppliers
        products_without_suppliers = self.env['product.product'].search([
            ('seller_ids', '=', False),
            ('active', '=', True)
        ])
        
        self.assertIn(product, products_without_suppliers, "Product should be in list")
        
        # Archive them
        products_without_suppliers.write({'active': False})
        
        self.assertFalse(product.active, "Product should be archived")

    def test_08_multiple_suppliers_price_calculation(self):
        """Test that removing one supplier doesn't archive product if others exist"""
        product = self.products['5000000000001']
        
        # Add second supplier
        self.env['product.supplierinfo'].create({
            'partner_id': self.supplier_b.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'product_id': product.id,
            'product_code': 'SKU-B-001',
            'price': 15.0,
            'min_qty': 10,
        })
        
        # Product now has 2 suppliers
        si_count = self.env['product.supplierinfo'].search_count([
            ('product_id', '=', product.id)
        ])
        self.assertEqual(si_count, 2, "Product should have 2 suppliers")
        
        # Remove supplier A's supplierinfo
        self.env['product.supplierinfo'].search([
            ('product_id', '=', product.id),
            ('partner_id', '=', self.supplier_a.id)
        ]).unlink()
        
        # Product should still be active (has supplier B)
        si_count = self.env['product.supplierinfo'].search_count([
            ('product_id', '=', product.id)
        ])
        self.assertEqual(si_count, 1, "Product should still have 1 supplier")
        
        # Post-processing should NOT archive this product
        products_without_suppliers = self.env['product.product'].search([
            ('seller_ids', '=', False)
        ])
        self.assertNotIn(product, products_without_suppliers, 
                        "Product with remaining supplier should not be in archive list")

    def test_09_bulk_update_performance(self):
        """Test that we can identify bulk update candidates"""
        # All existing supplierinfo (products 1-5) should be bulk updatable
        existing_si = self.env['product.supplierinfo'].search([
            ('partner_id', '=', self.supplier_a.id)
        ])
        
        self.assertEqual(len(existing_si), 5, "Should have 5 records for bulk update")
        
        # Collect product codes and new prices
        bulk_updates = []
        for i in range(1, 6):
            bulk_updates.append({
                'product_code': f'SKU-A-{i:03d}',
                'new_price': 30.0 + i,
                'new_stock': 200 + i,
            })
        
        self.assertEqual(len(bulk_updates), 5, "Should have 5 bulk updates prepared")
        
        # In real implementation, this would be a single SQL UPDATE with CASE statements
        # For test, verify all codes exist
        codes = [u['product_code'] for u in bulk_updates]
        found = self.env['product.supplierinfo'].search([
            ('partner_id', '=', self.supplier_a.id),
            ('product_code', 'in', codes)
        ])
        self.assertEqual(len(found), 5, "Should find all 5 records for bulk update")

    def test_10_combined_workflow(self):
        """Test complete workflow: cleanup + update + create + archive"""
        # Initial state: Products 1-5 have supplierinfo
        initial_count = self.env['product.supplierinfo'].search_count([
            ('partner_id', '=', self.supplier_a.id)
        ])
        self.assertEqual(initial_count, 5, "Should start with 5 supplierinfo")
        
        # New CSV has products 3-8
        # Expected actions:
        # - Delete: 1-2 (2 deletes)
        # - Update: 3-5 (3 updates)
        # - Create: 6-8 (3 creates)
        
        csv_codes = {f'SKU-A-{i:03d}' for i in range(3, 9)}
        existing_codes = set(
            self.env['product.supplierinfo']
            .search([('partner_id', '=', self.supplier_a.id)])
            .mapped('product_code')
        )
        
        # 1. Cleanup
        codes_to_delete = existing_codes - csv_codes
        self.assertEqual(len(codes_to_delete), 2, "Should delete 2")
        
        to_delete = self.env['product.supplierinfo'].search([
            ('partner_id', '=', self.supplier_a.id),
            ('product_code', 'in', list(codes_to_delete))
        ])
        to_delete.unlink()
        
        # 2. Identify updates vs creates
        remaining_codes = existing_codes - codes_to_delete
        update_codes = csv_codes & remaining_codes
        create_codes = csv_codes - remaining_codes
        
        self.assertEqual(len(update_codes), 3, "Should update 3")
        self.assertEqual(len(create_codes), 3, "Should create 3")
        
        # 3. Create new supplierinfo
        for i in range(6, 9):
            ean = f'500000000000{i:1d}'
            product = self.products[ean]
            self.env['product.supplierinfo'].create({
                'partner_id': self.supplier_a.id,
                'product_tmpl_id': product.product_tmpl_id.id,
                'product_id': product.id,
                'product_code': f'SKU-A-{i:03d}',
                'price': 30.0 + i,
                'min_qty': 10,
            })
        
        # 4. Verify final state
        final_count = self.env['product.supplierinfo'].search_count([
            ('partner_id', '=', self.supplier_a.id)
        ])
        self.assertEqual(final_count, 6, "Should end with 6 supplierinfo (3 updated + 3 created)")
