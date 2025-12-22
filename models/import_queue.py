# -*- coding: utf-8 -*-
"""
Import Queue - Background processing for large imports
"""

from odoo import models, fields, api
import base64
import csv
import io
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
    state = fields.Selection([
        ('queued', 'In Wachtrij'),
        ('processing', 'Bezig'),
        ('done', 'Voltooid'),
        ('failed', 'Mislukt'),
    ], string='Status', default='queued', required=True)
    
    @api.model
    def _process_queue(self):
        """
        Cron job method: Process queued imports one by one
        This method is called by the scheduled action
        """
        # Check if there's already an import being processed
        processing_items = self.search([('state', '=', 'processing')])
        
        # Check for stuck imports (no batch progress for more than 15 minutes)
        # Uses history write_date which is updated every batch (500 rows)
        # Kortere timeout = snellere recovery na server restart
        if processing_items:
            from datetime import datetime, timedelta
            fifteen_mins_ago = fields.Datetime.now() - timedelta(minutes=15)
            stuck_items = processing_items.filtered(
                lambda i: i.history_id and i.history_id.write_date and i.history_id.write_date < fifteen_mins_ago
            )
            
            if stuck_items:
                _logger.warning(f'Found {len(stuck_items)} stuck import(s) (no progress >15min), attempting recovery: {stuck_items.ids}')
                for item in stuck_items:
                    # Check if we should retry or fail
                    retry_count = item.history_id.retry_count or 0
                    
                    if retry_count < 3:
                        # Reset to queued for retry
                        _logger.info(f'Retry {retry_count + 1}/3 for import {item.id}')
                        item.write({'state': 'queued'})
                        item.history_id.write({
                            'state': 'pending',
                            'retry_count': retry_count + 1,
                            'summary': f'Import restarted na timeout (poging {retry_count + 1}/3)'
                        })
                    else:
                        # Failed after 3 retries
                        _logger.error(f'Import {item.id} failed after 3 retries')
                        item.write({'state': 'failed'})
                        item.history_id.write({
                            'state': 'failed',
                            'summary': 'Import gefaald na 3 pogingen (server restarts of timeout)'
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
            
            # Mark as done - alleen nu last_sync_date updaten bij succesvolle import!
            queue_item.state = 'done'
            
            # Update supplier last sync date ALLEEN bij succesvolle import
            if queue_item.supplier_id:
                queue_item.supplier_id.sudo().write({
                    'last_sync_date': fields.Datetime.now()
                })
                _logger.info(f"✅ Supplier {queue_item.supplier_id.name} last_sync_date updated")
            
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
        """Execute the import from queue data"""
        self.ensure_one()
        
        # Parse mapping from string
        mapping = ast.literal_eval(self.mapping)
        
        start_time = time.time()
        
        try:
            # STAP 1: Archiveer alle oude supplierinfo van deze leverancier
            archived_count = self.env['product.supplierinfo'].archive_old_supplier_products(self.supplier_id.id)
            _logger.info(f"Archived {archived_count} old supplierinfo records for {self.supplier_id.name}")
            
            # Parse CSV
            csv_data = base64.b64decode(self.csv_file).decode(self.encoding)
            csv_reader = csv.DictReader(io.StringIO(csv_data), delimiter=self.csv_separator)
            
            # Process rows
            stats = {
                'total': 0,
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'errors': [],
                'history_id': self.history_id.id
            }
            
            # Batch processing
            BATCH_SIZE = 500
            batch_count = 0
            
            # Get direct import model for processing logic
            DirectImport = self.env['supplier.direct.import']
            
            for row_num, row in enumerate(csv_reader, start=2):
                stats['total'] += 1
                
                try:
                    # Use DirectImport's _process_row method
                    # Create temporary wizard instance with supplier context
                    temp_wizard = DirectImport.create({
                        'supplier_id': self.supplier_id.id,
                        'csv_file': self.csv_file,
                        'csv_filename': self.csv_filename,
                    })
                    temp_wizard._process_row(row, mapping, stats, row_num)
                    temp_wizard.unlink()  # Clean up temp wizard
                    
                except Exception as e:
                    error_msg = str(e) if str(e) else f"{type(e).__name__} (geen error message)"
                    stats['errors'].append(f"Rij {row_num}: {error_msg}")
                    stats['skipped'] += 1
                    _logger.error(f"Background import error on row {row_num}: {error_msg}", exc_info=True)
                
                # Commit after each batch
                if stats["total"] % BATCH_SIZE == 0:
                    batch_count += 1
                    
                    # Update history with current progress
                    self.history_id.write({
                        'total_rows': stats['total'],
                        'created_count': stats['created'],
                        'updated_count': stats['updated'],
                        'skipped_count': stats['skipped'],
                        'error_count': len(stats['errors']),
                        'duration': time.time() - start_time,
                        'summary': f"Processing... {stats['total']} rows processed so far ({stats['created']} created, {stats['updated']} updated, {stats['skipped']} skipped, {len(stats['errors'])} errors)",
                        'state': 'running',
                    })
                    self.env.cr.commit()
                    
                    _logger.info(f"Background import batch {batch_count} committed ({stats['total']} rows, {stats['created']} created, {stats['skipped']} skipped)")
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Create summary
            DirectImport = self.env['supplier.direct.import']
            temp_wizard = DirectImport.create({
                'supplier_id': self.supplier_id.id,
                'csv_file': self.csv_file,
            })
            summary = temp_wizard._create_import_summary(stats)
            
            # AUTO-SAVE mapping template (same as direct import)
            temp_wizard._auto_save_mapping_template(mapping)
            
            temp_wizard.unlink()
            
            # Update history record
            self.history_id.write({
                'total_rows': stats['total'],
                'created_count': stats['created'],
                'updated_count': stats['updated'],
                'skipped_count': stats['skipped'],
                'error_count': len(stats['errors']),
                'duration': duration,
                'summary': summary,
                'state': 'completed_with_errors' if stats['errors'] else 'completed',
            })
            # STAP 3: Archiveer/de-archiveer producten op basis van suppliers (alleen bij succes)
            if not stats['errors']:
                archived, unarchived = self.env['product.supplierinfo'].check_and_archive_products_without_suppliers()
                if archived or unarchived:
                    _logger.info(f"Product archivering: {archived} gearchiveerd, {unarchived} gereactiveerd")
                        # Update supplier's last sync date
            try:
                self.supplier_id.write({'last_sync_date': fields.Datetime.now()})
            except Exception as e:
                _logger.warning(f"Could not update supplier last_sync_date: {e}")
            
            _logger.info(f"Background import completed: {stats['total']} rows processed, {stats['created']} created, {stats['updated']} updated")
            
        except Exception as e:
            _logger.error(f"Background import failed: {e}", exc_info=True)
            raise
