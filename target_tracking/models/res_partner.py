from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'

    district = fields.Char(
        string='District',
        help='District or region for grouping customers'
    )
    
    # Target fields
    target_start_date = fields.Date(
        string='Start Date',
        help='Start date of the target period',
        default=lambda self: self._get_default_start_date()
    )
    
    target_end_date = fields.Date(
        string='End Date',
        help='End date of the target period',
        default=lambda self: self._get_default_end_date()
    )
    
    sales_representative_id = fields.Many2one(
        'hr.employee',
        string='Sales Representative',
        help='Sales representative from employees'
    )
    
    target = fields.Float(
        string='Target',
        default=0.0
    )
    
    target_achieved = fields.Float(
        string='Target Achieved',
        compute='_compute_target_achieved',
        store=True
    )
    
    pending_target = fields.Float(
        string='Pending Target',
        compute='_compute_pending_target',
        store=True
    )
    
    @api.model
    def _get_default_start_date(self):
        """Get the first day of the current month"""
        today = datetime.today()
        return today.replace(day=1).date()
    
    @api.model
    def _get_default_end_date(self):
        """Get the last day of the current month"""
        today = datetime.today()
        next_month = today.replace(day=1) + relativedelta(months=1)
        last_day = next_month - relativedelta(days=1)
        return last_day.date()
    
    @api.depends('target')
    def _compute_target_achieved(self):
        """Compute target achieved from target tracking records"""
        for partner in self:
            tracking_record = self.env['target.tracking'].search([
                ('partner_id', '=', partner.id)
            ], limit=1, order='date_from desc')
            partner.target_achieved = tracking_record.target_achieved if tracking_record else 0.0
    
    @api.depends('target', 'target_achieved')
    def _compute_pending_target(self):
        """Compute pending target"""
        for partner in self:
            partner.pending_target = partner.target - partner.target_achieved

    def write(self, vals):
        """Update target tracking records when partner is updated"""
        result = super(ResPartner, self).write(vals)
        
        # Auto-create target.tracking.state if state_id is set on a customer
        if 'state_id' in vals:
            for partner in self:
                if partner.customer_rank > 0 and partner.state_id:
                    # Check if state already exists in target.tracking.state
                    existing_state = self.env['target.tracking.state'].search([
                        ('state_id', '=', partner.state_id.id)
                    ], limit=1)
                    
                    # Create if doesn't exist
                    if not existing_state:
                        self.env['target.tracking.state'].create({
                            'state_id': partner.state_id.id
                        })
        
        # Sync target fields to target.tracking
        target_fields = ['target_start_date', 'target_end_date', 'sales_representative_id', 'target', 'district']
        if any(field in vals for field in target_fields):
            for partner in self:
                if partner.customer_rank > 0:  # Only for customers
                    # Prepare values for sync
                    sync_vals = {
                        'partner_id': partner.id,
                        'date_from': partner.target_start_date or fields.Date.today(),
                        'date_to': partner.target_end_date or fields.Date.today(),
                        'sales_representative_id': partner.sales_representative_id.id if partner.sales_representative_id else False,
                        'jan_target': partner.target or 0.0,
                        'district': partner.district or '',
                        'taluka_name': partner.city or '',
                        'phone': partner.phone or '',
                        'state_id': partner.state_id.id if partner.state_id else False,
                        'salesperson_id': partner.user_id.id if partner.user_id else False,
                    }
                    
                    # Find target tracking record for the current date range
                    tracking_record = self.env['target.tracking'].search([
                        ('partner_id', '=', partner.id),
                        ('date_from', '=', partner.target_start_date),
                        ('date_to', '=', partner.target_end_date)
                    ], limit=1)
                    
                    if tracking_record:
                        # Update existing record for this date range
                        tracking_record.write(sync_vals)
                    else:
                        # Create new tracking record for this date range
                        self.env['target.tracking'].create(sync_vals)
        
        # Update related target tracking records if district, name, phone, or parent changes
        if any(field in vals for field in ['name', 'phone', 'parent_id', 'city', 'state_id', 'user_id']):
            for partner in self:
                tracking_records = self.env['target.tracking'].search([('partner_id', '=', partner.id)])
                # The related fields will auto-update, but we trigger a recompute
                if tracking_records:
                    tracking_records._compute_pending_target()
        
        return result

    def unlink(self):
        """Delete related target tracking records when partner is deleted"""
        # Find and delete related target tracking records
        tracking_records = self.env['target.tracking'].search([('partner_id', 'in', self.ids)])
        tracking_records.unlink()
        
        return super(ResPartner, self).unlink()
    
    @api.model
    def _cron_reset_target_monthly(self):
        """Scheduled action to reset target dates and values at the end of each month"""
        today = fields.Date.today()
        
        # Get all customers with target data
        customers = self.search([
            ('customer_rank', '>', 0),
            ('target_end_date', '!=', False)
        ])
        
        for customer in customers:
            # Check if the target end date has passed
            if customer.target_end_date and customer.target_end_date < today:
                # Calculate next month's dates
                next_month_start = today.replace(day=1)
                next_month_end = (next_month_start + relativedelta(months=1)) - relativedelta(days=1)
                
                # Update to next month and reset target to 0
                customer.write({
                    'target_start_date': next_month_start,
                    'target_end_date': next_month_end,
                    'target': 0.0
                })
