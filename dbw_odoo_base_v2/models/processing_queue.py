# -*- coding: utf-8 -*-
from odoo import models, fields, api
import json
import logging

_logger = logging.getLogger(__name__)


class DbwProcessingQueue(models.Model):
    """
    Central processing queue for all DBW modules.
    
    Enables pipeline orchestration:
    - Supplier import → Quality validation → Pricing → Publish
    
    Features:
    - Priority-based execution
    - Automatic retries
    - Scheduled execution
    - Event-triggered chaining (queue next step on completion)
    - Persistent history
    """
    
    _name = 'dbw.processing.queue'
    _description = 'DBW Processing Queue'
    _order = 'priority desc, scheduled_date asc, create_date asc'
    
    # Identification
    name = fields.Char(
        string='Task Name',
        required=True,
        readonly=True,
        compute='_compute_name',
        store=True
    )
    
    # What to execute
    model_name = fields.Char(
        string='Model',
        required=True,
        help='Model to call: supplier.import.schedule, icecat.sync, quality.validator'
    )
    
    method_name = fields.Char(
        string='Method',
        required=True,
        help='Method to call on the model: execute_import, validate_products, recalculate_pricing'
    )
    
    # When to execute
    priority = fields.Selection(
        [
            ('low', '🟢 Low'),
            ('normal', '🟡 Normal'),
            ('high', '🔴 High'),
            ('urgent', '⚫ Urgent'),
        ],
        string='Priority',
        default='normal',
        required=True
    )
    
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('queued', 'Queued'),
            ('processing', 'Processing'),
            ('done', 'Done'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        string='State',
        default='draft',
        required=True
    )
    
    scheduled_date = fields.Datetime(
        string='Scheduled For',
        help='null = execute ASAP'
    )
    
    # Execution tracking
    created_date = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True
    )
    
    started_date = fields.Datetime(
        readonly=True
    )
    
    completed_date = fields.Datetime(
        readonly=True
    )
    
    duration_seconds = fields.Float(
        string='Duration (seconds)',
        compute='_compute_duration',
        store=False
    )
    
    # Retry logic
    retry_count = fields.Integer(
        default=0,
        readonly=True
    )
    
    max_retries = fields.Integer(
        default=3,
        help='Max retries on failure'
    )
    
    last_error = fields.Text(
        readonly=True,
        help='Last error message'
    )
    
    # Data
    arguments = fields.Json(
        default=dict,
        help='Method arguments: {product_ids: [1,2,3], action: "validate"}'
    )
    
    result = fields.Json(
        readonly=True,
        help='Method output'
    )
    
    # Pipeline orchestration - CORE FEATURE!
    next_queue_id = fields.Many2one(
        'dbw.processing.queue',
        string='Next Task (Chain)',
        help='Automatically queue this task when current completes'
    )
    
    triggered_by_id = fields.Many2one(
        'dbw.processing.queue',
        string='Triggered By',
        readonly=True,
        help='Which task triggered this one?'
    )
    
    # Tracking
    processed_by = fields.Many2one(
        'res.users',
        readonly=True,
        default=lambda self: self.env.user
    )
    
    # Logs
    log_ids = fields.One2many(
        'dbw.processing.queue.log',
        'queue_id',
        string='Logs'
    )
    
    # Related records (for context)
    product_ids = fields.Many2many(
        'product.template',
        string='Products (affected)',
        readonly=True
    )
    
    @api.depends('model_name', 'method_name', 'scheduled_date')
    def _compute_name(self):
        """Auto-generate task name"""
        for record in self:
            method_short = record.method_name[:20] if record.method_name else 'task'
            time_str = record.scheduled_date.strftime('%H:%M') if record.scheduled_date else 'ASAP'
            record.name = f"{record.model_name}.{method_short}() @ {time_str}"
    
    @api.depends('started_date', 'completed_date')
    def _compute_duration(self):
        """Calculate execution time"""
        for record in self:
            if record.started_date and record.completed_date:
                delta = record.completed_date - record.started_date
                record.duration_seconds = delta.total_seconds()
            else:
                record.duration_seconds = 0
    
    def action_queue(self):
        """Move from draft to queued"""
        self.write({'state': 'queued'})
    
    def action_execute_now(self):
        """Execute immediately (don't wait for scheduler)"""
        self.ensure_one()
        self.execute()
    
    def execute(self):
        """
        Execute the queued task.
        Called by: cron job OR manually.
        """
        self.ensure_one()
        
        if self.state not in ['queued', 'draft']:
            _logger.warning(f"Task {self.id} not in queued/draft state: {self.state}")
            return
        
        self.write({
            'state': 'processing',
            'started_date': fields.Datetime.now()
        })
        
        _logger.info(f"🚀 Executing task {self.id}: {self.model_name}.{self.method_name}")
        
        try:
            # Dynamic method calling
            model = self.env[self.model_name]
            method = getattr(model, self.method_name, None)
            
            if not method:
                raise ValueError(f"Method {self.method_name} not found on {self.model_name}")
            
            # Call the method with arguments
            result = method(**self.arguments)
            
            # Mark as done
            self.write({
                'state': 'done',
                'completed_date': fields.Datetime.now(),
                'result': json.dumps(result, default=str)
            })
            
            _logger.info(f"✅ Task {self.id} completed successfully")
            
            # PIPELINE ORCHESTRATION: Trigger next task!
            self._trigger_next_task()
            
        except Exception as e:
            error_msg = str(e)
            _logger.error(f"❌ Task {self.id} failed: {error_msg}")
            self._handle_error(error_msg)
    
    def _trigger_next_task(self):
        """
        If next_queue_id is set, queue and execute it.
        This is the ORCHESTRATION magic!
        """
        if self.next_queue_id:
            _logger.info(f"⛓️  Triggering next task: {self.next_queue_id.name}")
            
            # Update the next task
            self.next_queue_id.write({
                'state': 'queued',
                'triggered_by_id': self.id,
            })
            
            # Execute immediately OR schedule for later?
            # Option 1: Execute now (tight coupling)
            # self.next_queue_id.execute()
            
            # Option 2: Queue for next cron run (loose coupling) ← RECOMMENDED
            # Let the scheduler pick it up
            
            _logger.info(f"⛓️  Next task {self.next_queue_id.id} queued")
    
    def _handle_error(self, error_msg):
        """Handle failed task"""
        should_retry = self.retry_count < self.max_retries
        
        if should_retry:
            # Retry
            self.write({
                'state': 'queued',  # Re-queue
                'retry_count': self.retry_count + 1,
                'last_error': error_msg,
                'scheduled_date': fields.Datetime.now(),  # Try again soon
            })
            _logger.warning(f"🔄 Retrying task {self.id} (attempt {self.retry_count + 1}/{self.max_retries})")
        else:
            # Give up
            self.write({
                'state': 'failed',
                'completed_date': fields.Datetime.now(),
                'last_error': error_msg,
            })
            _logger.error(f"💥 Task {self.id} failed after {self.max_retries} retries")
    
    def action_retry(self):
        """Manual retry"""
        self.write({
            'state': 'queued',
            'retry_count': 0,
            'last_error': None,
            'started_date': None,
            'completed_date': None,
        })
    
    def action_cancel(self):
        """Cancel task"""
        self.write({'state': 'cancelled'})
    
    @api.model
    def cron_process_queue(self):
        """
        CRON JOB: Process queued tasks.
        Schedule: Every 5 minutes
        """
        _logger.info("⏰ Queue processor cron started")
        
        # Find tasks ready to process
        # Include ASAP tasks (scheduled_date = NULL) AND tasks where time has come
        ready_tasks = self.search([
            ('state', '=', 'queued'),
            '|',  # OR operator
                ('scheduled_date', '=', False),  # ASAP tasks
                ('scheduled_date', '<=', fields.Datetime.now()),  # Scheduled tasks due
        ], order='priority desc, create_date asc', limit=5)
        
        if not ready_tasks:
            _logger.info("📭 No tasks in queue")
            return
        
        _logger.info(f"🔄 Processing {len(ready_tasks)} tasks")
        
        for task in ready_tasks:
            try:
                task.execute()
            except Exception as e:
                _logger.error(f"Cron error processing task {task.id}: {e}")
        
        _logger.info("✅ Queue processor cron completed")
    
    @api.model
    def check_scheduled_imports(self):
        """
        CRON JOB: Check if scheduled supplier imports need to run.
        Schedule: Every hour
        
        Checks all active supplier.import.schedule records and triggers imports
        that are due based on schedule_type (daily, weekly, monthly) and schedule_time.
        """
        _logger.info("⏰ Checking scheduled imports...")
        
        # Check if supplier.import.schedule model exists
        if 'supplier.import.schedule' not in self.env:
            _logger.debug("supplier.import.schedule model not found (module not installed)")
            return
        
        try:
            # Get all active scheduled imports
            SupplierSchedule = self.env['supplier.import.schedule']
            schedules = SupplierSchedule.search([
                ('active', '=', True),
                ('schedule_type', '!=', False)
            ])
            
            if not schedules:
                _logger.info("📭 No active scheduled imports found")
                return
            
            _logger.info(f"🔍 Found {len(schedules)} active schedules")
            
            from datetime import datetime, timedelta
            now = datetime.now()
            triggered_count = 0
            
            for schedule in schedules:
                try:
                    # Determine if this schedule should run
                    should_run = False
                    schedule_name = schedule.name or f"Schedule #{schedule.id}"
                    
                    # If never run, run now
                    if not schedule.last_run:
                        _logger.info(f"📌 {schedule_name}: Never run before, triggering now")
                        should_run = True
                    else:
                        last_run = schedule.last_run
                        schedule_time_hour = int(schedule.schedule_time or 2)
                        schedule_time_minute = int((schedule.schedule_time % 1) * 60)
                        
                        # Calculate next scheduled run based on schedule_type
                        if schedule.schedule_type == 'daily':
                            # Daily: Run once per day at schedule_time
                            next_run = last_run.replace(
                                hour=schedule_time_hour,
                                minute=schedule_time_minute,
                                second=0,
                                microsecond=0
                            )
                            # If we already ran today, schedule for tomorrow
                            if next_run <= last_run:
                                next_run += timedelta(days=1)
                            
                            if now >= next_run:
                                _logger.info(f"📅 {schedule_name}: Daily schedule due (last: {last_run}, next: {next_run})")
                                should_run = True
                        
                        elif schedule.schedule_type == 'weekly':
                            # Weekly: Run on specific day_of_week
                            day_of_week = int(schedule.schedule_day_of_week or 0)  # 0=Monday
                            next_run = last_run.replace(
                                hour=schedule_time_hour,
                                minute=schedule_time_minute,
                                second=0,
                                microsecond=0
                            )
                            # Find next occurrence of day_of_week
                            days_ahead = day_of_week - next_run.weekday()
                            if days_ahead <= 0:  # Target day already passed this week
                                days_ahead += 7
                            next_run += timedelta(days=days_ahead)
                            
                            if now >= next_run:
                                _logger.info(f"📅 {schedule_name}: Weekly schedule due (last: {last_run}, next: {next_run})")
                                should_run = True
                        
                        elif schedule.schedule_type == 'monthly':
                            # Monthly: Run on specific day_of_month
                            day_of_month = int(schedule.schedule_day_of_month or 1)
                            next_run = last_run.replace(
                                day=min(day_of_month, 28),  # Safely handle month lengths
                                hour=schedule_time_hour,
                                minute=schedule_time_minute,
                                second=0,
                                microsecond=0
                            )
                            # If this month's date passed, go to next month
                            if next_run <= last_run:
                                # Add one month (approximate)
                                if next_run.month == 12:
                                    next_run = next_run.replace(year=next_run.year + 1, month=1)
                                else:
                                    next_run = next_run.replace(month=next_run.month + 1)
                            
                            if now >= next_run:
                                _logger.info(f"📅 {schedule_name}: Monthly schedule due (last: {last_run}, next: {next_run})")
                                should_run = True
                    
                    # Trigger import if due
                    if should_run:
                        if hasattr(schedule, 'action_run_import_now'):
                            _logger.info(f"🚀 Triggering import for: {schedule_name}")
                            schedule.action_run_import_now()
                            triggered_count += 1
                        else:
                            _logger.warning(f"⚠️  {schedule_name}: action_run_import_now method not found")
                
                except Exception as e:
                    _logger.error(f"❌ Error checking schedule {schedule.id}: {e}")
                    continue
            
            if triggered_count > 0:
                _logger.info(f"✅ Triggered {triggered_count} scheduled import(s)")
            else:
                _logger.info("✅ All schedules are up to date")
        
        except Exception as e:
            _logger.error(f"❌ Error in check_scheduled_imports: {e}")


class DbwProcessingQueueLog(models.Model):
    """
    Execution logs for each task.
    Useful for debugging and audit trail.
    """
    
    _name = 'dbw.processing.queue.log'
    _description = 'Processing Queue Log'
    _order = 'create_date desc'
    
    queue_id = fields.Many2one(
        'dbw.processing.queue',
        required=True,
        ondelete='cascade'
    )
    
    level = fields.Selection(
        [
            ('debug', '🔵 Debug'),
            ('info', '🟢 Info'),
            ('warning', '🟡 Warning'),
            ('error', '🔴 Error'),
        ],
        required=True
    )
    
    message = fields.Text(required=True)
    
    create_date = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True
    )
