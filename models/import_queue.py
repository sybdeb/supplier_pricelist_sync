# -*- coding: utf-8 -*-
"""
Import Queue - Background processing for large imports
"""

from odoo import models, fields, api
import time
import logging
import ast

_logger = logging.getLogger(__name__)


class SupplierImportQueue(models.Model):
    """Queue model for background import processing"""
    _name = 'supplier.import.queue'
    _description = 'Supplier Import Queue'
    _order = 'create_date desc'
    
    history_id = fields.Many2one('supplier.import.history', string='Import History', required=True, ondelete='cascade')
    supplier_id = fields.Many2one('res.partner', string='Supplier', required=True)
    csv_file = fields.Binary(string='CSV File', required=True)
    csv_filename = fields.Char(string='Filename')
    encoding = fields.Char(string='Encoding', default='utf-8')
    csv_separator = fields.Char(string='Separator', default=';')
    mapping = fields.Text(string='Column Mapping', required=True)
    
    # Filter settings
    min_stock_qty = fields.Integer(string='Minimum Stock Qty', default=0)
    min_price = fields.Float(string='Minimum Price', default=0.0)
    skip_discontinued = fields.Boolean(string='Skip Discontinued', default=False)
    brand_blacklist_ids = fields.Many2many(
        'product.brand',
        relation='queue_brand_blacklist_rel',
        column1='queue_id',
        column2='brand_id',
        string='Merk Blacklist'
    )
    ean_whitelist = fields.Text(string='EAN Whitelist (1 per regel)')
    
    state = fields.Selection([
        ('queued', 'In Wachtrij'),
        ('processing', 'Bezig'),
        ('done', 'Voltooid'),
        ('failed', 'Mislukt'),
    ], string='Status', default='queued', required=True)
    
    @api.model
    def _cleanup_old_queue_records(self):
        """
        Cron job: Cleanup oude queue records (ouder dan 30 dagen).
        Alleen 'done' en 'failed' records worden verwijderd.
        """
        from datetime import timedelta
        cleanup_date = fields.Datetime.now() - timedelta(days=30)
        
        old_records = self.search([
            ('state', 'in', ['done', 'failed']),
            ('create_date', '<', cleanup_date)
        ])
        
        if old_records:
            _logger.info(f"Cleanup: Verwijderen {len(old_records)} oude queue records (>30 dagen)")
            old_records.unlink()
        
        return True
    
    @api.model
    def _process_queue(self):
        """
        Cron job method: Process queued imports one by one
        This method is called by the scheduled action
        """
        # Check if there's already an import being processed
        processing_items = self.search([('state', '=', 'processing')])
        
        # Check for stuck imports (no batch progress for more than 1 hour)
        # Uses history write_date which is updated every batch (500 rows)
        if processing_items:
            from datetime import timedelta
            one_hour_ago = fields.Datetime.now() - timedelta(hours=1)
            stuck_items = processing_items.filtered(
                lambda i: i.history_id and i.history_id.write_date and i.history_id.write_date < one_hour_ago
            )
            
            if stuck_items:
                _logger.warning(f'Found {len(stuck_items)} stuck import(s) (no batch progress >1h), marking as failed: {stuck_items.ids}')
                for item in stuck_items:
                    item.write({'state': 'failed'})
                    item.history_id.write({
                        'state': 'failed',
                        'summary': 'Import timeout: No batch progress for more than 1 hour (mogelijk vastgelopen)'
                    })
                # Refresh processing_items list
                processing_items = self.search([('state', '=', 'processing')])
        
        if processing_items:
            _logger.info(f'{len(processing_items)} import(s) already processing, waiting... Import IDs: {processing_items.ids}')
            return
        
        # Find next queued import
        queue_item = self.search([('state', '=', 'queued')], limit=1, order='create_date asc')
        
        if not queue_item:
            _logger.info("No queued imports to process")
            return
        
        _logger.info(f"Processing queued import {queue_item.id} for supplier {queue_item.supplier_id.name}")
        
        try:
            # Mark as processing
            queue_item.state = 'processing'
            queue_item.history_id.state = 'running'
            self.env.cr.commit()
            
            # Execute import
            queue_item._execute_queued_import()
            
            # Mark as done
            queue_item.state = 'done'
            self.env.cr.commit()
            
        except Exception as e:
            _logger.error(f"Failed to process queued import {queue_item.id}: {e}", exc_info=True)
            queue_item.state = 'failed'
            queue_item.history_id.write({
                'state': 'failed',
                'summary': f"Background import failed: {str(e)}",
            })
            self.env.cr.commit()
    
    def _execute_queued_import(self):
        """Execute the import from queue data - NIEUWE BULK ARCHITECTUUR"""
        self.ensure_one()
        
        # Parse mapping from string
        mapping = ast.literal_eval(self.mapping)
        
        _logger.info(f"Starting background import with NEW BULK architecture for supplier {self.supplier_id.name}")
        
        # AUTO-SAVE mapping VOOR import start (zodat mapping altijd wordt opgeslagen)
        DirectImport = self.env['supplier.direct.import']
        temp_wizard_for_save = DirectImport.create({
            'supplier_id': self.supplier_id.id,
        })
        temp_wizard_for_save._auto_save_mapping_template(mapping)
        temp_wizard_for_save.unlink()
        
        try:
            # Create temporary wizard instance to use the new bulk import methods
            DirectImport = self.env['supplier.direct.import']
            _logger.info(f"DEBUG QUEUE: Queue has brand_blacklist_ids count = {len(self.brand_blacklist_ids)}, IDs = {self.brand_blacklist_ids.ids}")
            temp_wizard = DirectImport.create({
                'supplier_id': self.supplier_id.id,
                'csv_file': self.csv_file,
                'csv_filename': self.csv_filename,
                'encoding': self.encoding,
                'csv_separator': self.csv_separator,
                'min_stock_qty': self.min_stock_qty,
                'min_price': self.min_price,
                'skip_discontinued': self.skip_discontinued,
                'brand_blacklist_ids': [(6, 0, self.brand_blacklist_ids.ids)],
                'ean_whitelist': self.ean_whitelist or '',
            })
            _logger.info(f"DEBUG WIZARD: Created temp_wizard with brand_blacklist_ids count = {len(temp_wizard.brand_blacklist_ids)}, IDs = {temp_wizard.brand_blacklist_ids.ids}")
            
            # Save the original history reference
            original_history = self.history_id
            
            # Call the NEW bulk _execute_import method
            import json
            start_time = time.time()
            
            # STEP 1: PRE-SCAN CSV
            _logger.info("=== BACKGROUND IMPORT: STEP 1 PRE-SCAN ===")
            prescan_data = temp_wizard._prescan_csv_and_prepare(mapping)
            
            total_rows = len(prescan_data['update_codes']) + len(prescan_data['create_codes']) + \
                        len(prescan_data['filtered']) + len(prescan_data['error_rows'])
            
            _logger.info(f"Pre-scan: {total_rows} rows ({len(prescan_data['update_codes'])} updates, {len(prescan_data['create_codes'])} creates)")
            
            # STEP 2: CLEANUP
            _logger.info("=== BACKGROUND IMPORT: STEP 2 CLEANUP ===")
            cleanup_stats = temp_wizard._cleanup_old_supplierinfo(prescan_data, original_history.id)
            
            # STEP 3: BULK UPDATE
            updated_count = 0
            if prescan_data['update_codes']:
                _logger.info("=== BACKGROUND IMPORT: STEP 3 BULK UPDATE ===")
                updated_count = temp_wizard._bulk_update_supplierinfo(prescan_data, mapping)
            
            # STEP 4: BULK CREATE
            created_count = 0
            if prescan_data['create_codes']:
                _logger.info("=== BACKGROUND IMPORT: STEP 4 BULK CREATE ===")
                created_count = temp_wizard._bulk_create_supplierinfo(prescan_data, mapping)
            
            # STEP 5: POST-PROCESS
            _logger.info("=== BACKGROUND IMPORT: STEP 5 POST-PROCESS ===")
            archived_count = temp_wizard._archive_products_without_suppliers()
            reactivated_count = temp_wizard._reactivate_products_with_suppliers(prescan_data)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Build summary with skip reasons
            stats = {
                'total': total_rows,
                'created': created_count,
                'updated': updated_count,
                'skipped': len(prescan_data['filtered']),
                'errors': prescan_data['error_rows'],
                'skip_reasons': prescan_data.get('skip_reasons', {}),  # Add skip reasons breakdown
            }
            summary = temp_wizard._create_import_summary(stats)
            
            # Add cleanup stats to summary
            summary += f"\n\nCleanup:\n" \
                      f"- Verwijderd: {cleanup_stats['removed']} oude leverancier regels\n" \
                      f"- Gearchiveerd: {archived_count} producten (geen leveranciers + geen voorraad)\n" \
                      f"- Geactiveerd: {reactivated_count} producten (hebben weer leveranciers)"
            
            # Update history record
            original_history.write({
                'total_rows': total_rows,
                'created_count': created_count,
                'updated_count': updated_count,
                'skipped_count': len(prescan_data['filtered']),
                'error_count': len(prescan_data['error_rows']),
                'duration': duration,
                'summary': summary,
                'state': 'completed_with_errors' if prescan_data['error_rows'] else 'completed',
                'mapping_data': json.dumps(mapping),  # Archive mapping
            })
            
            # Create error records in database for missende producten
            if prescan_data['error_rows']:
                temp_wizard._create_error_records(original_history.id, prescan_data['error_rows'])
                _logger.info(f"Created {len(prescan_data['error_rows'])} error records in database")
            
            # Update supplier's last sync date
            try:
                self.supplier_id.write({'last_sync_date': fields.Datetime.now()})
            except Exception as e:
                _logger.warning(f"Could not update supplier last_sync_date: {e}")
            
            # Clean up temp wizard
            temp_wizard.unlink()
            
            _logger.info(f"=== BACKGROUND IMPORT COMPLETE: {duration:.1f}s, {total_rows/duration:.0f} rows/sec ===")
            
        except Exception as e:
            _logger.error(f"Background import failed: {e}", exc_info=True)
            raise
        except Exception as e:
            _logger.error(f"Background import failed: {e}", exc_info=True)
            raise
    
    def action_requeue(self):
        """Requeue failed or processing imports"""
        for record in self:
            if record.state in ['failed', 'processing']:
                record.write({'state': 'queued'})
                if record.history_id:
                    record.history_id.write({'state': 'pending'})
    
    def action_mark_failed(self):
        """Manually mark queued/processing imports as failed"""
        for record in self:
            if record.state in ['queued', 'processing']:
                record.write({'state': 'failed'})
                if record.history_id:
                    record.history_id.write({
                        'state': 'failed',
                        'summary': 'Handmatig gemarkeerd als mislukt door gebruiker'
                    })
