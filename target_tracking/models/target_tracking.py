from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class TargetTracking(models.Model):
    _name = 'target.tracking'
    _description = 'Customer Target Tracking'
    _order = 'district, taluka_name, date_from desc'

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer Name',
        required=True,
        domain="[('customer_rank', '>', 0)]",
        ondelete='cascade',
        index=True
    )
    
    date_from = fields.Date(
        string='Start Date',
        help='Start date of the target period',
        index=True,
        default=lambda self: self._get_default_date_from()
    )
    
    date_to = fields.Date(
        string='End Date',
        help='End date of the target period',
        index=True,
        default=lambda self: self._get_default_date_to()
    )
    
    taluka_name = fields.Char(
        string='Talukas Names',
        store=True,
        index=True
    )
    
    super_stockiest_id = fields.Many2one(
        'res.partner',
        string='Super Stockiest',
        domain="[('customer_rank', '>', 0)]",
        help='Select the super stockiest customer'
    )
    
    salesperson_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        domain="[('share', '=', False)]",
        help='Salesperson responsible for this target',
        index=True
    )
    
    sales_representative_id = fields.Many2one(
        'hr.employee',
        string='Sales Representative',
        help='Sales representative from employees',
        index=True
    )
    
    phone = fields.Char(
        string='Phone',
        store=True,
        index=True
    )
    
    district = fields.Char(
        string='District',
        store=True,
        index=True
    )
    
    state_id = fields.Many2one(
        'res.country.state',
        string='State',
        store=True,
        index=True
    )
    
    jan_target = fields.Float(
        string='Target',
        default=0.0
    )
    
    target_achieved = fields.Float(
        string='Target Achieved',
        default=0.0,
        readonly=True
    )
    
    pending_target = fields.Float(
        string='Pending Target',
        compute='_compute_pending_target',
        store=True
    )
    
    @api.model
    def _get_default_date_from(self):
        """Get the first day of the current month"""
        today = datetime.today()
        return today.replace(day=1).date()
    
    @api.model
    def _get_default_date_to(self):
        """Get the last day of the current month"""
        today = datetime.today()
        next_month = today.replace(day=1) + relativedelta(months=1)
        last_day = next_month - relativedelta(days=1)
        return last_day.date()

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Auto-populate district, taluka_name, phone, and state from partner when selected"""
        if self.partner_id:
            self.district = self.partner_id.district
            self.taluka_name = self.partner_id.city
            self.phone = self.partner_id.phone
            self.state_id = self.partner_id.state_id
    
    @api.depends('jan_target', 'target_achieved')
    def _compute_pending_target(self):
        """Compute pending target as jan_target - target_achieved"""
        for record in self:
            record.pending_target = record.jan_target - record.target_achieved
    
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-create target.tracking.state when creating target tracking records"""
        records = super(TargetTracking, self).create(vals_list)
        
        # Auto-create state records for new target tracking records
        for record in records:
            if record.state_id:
                # Check if state already exists
                existing_state = self.env['target.tracking.state'].search([
                    ('state_id', '=', record.state_id.id)
                ], limit=1)
                
                # Create if doesn't exist
                if not existing_state:
                    self.env['target.tracking.state'].create({
                        'state_id': record.state_id.id
                    })
        
        return records
    
    def write(self, vals):
        """Auto-create target.tracking.state when updating state_id"""
        result = super(TargetTracking, self).write(vals)
        
        # Auto-create state if state_id is being set/changed
        if 'state_id' in vals:
            for record in self:
                if record.state_id:
                    # Check if state already exists
                    existing_state = self.env['target.tracking.state'].search([
                        ('state_id', '=', record.state_id.id)
                    ], limit=1)
                    
                    # Create if doesn't exist
                    if not existing_state:
                        self.env['target.tracking.state'].create({
                            'state_id': record.state_id.id
                        })
        
        return result
    
    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        """Ensure date_to is greater than or equal to date_from"""
        for record in self:
            if record.date_from and record.date_to and record.date_to < record.date_from:
                raise ValidationError('End date must be greater than or equal to start date.')
    
    def recalculate_target_achieved(self):
        """Recalculate target achieved based on confirmed sale orders in date range"""
        for record in self:
            domain = [
                ('partner_id', '=', record.partner_id.id),
                ('state', 'in', ['sale', 'done'])
            ]
            
            # Add date filters if date range is specified
            if record.date_from:
                domain.append(('date_order', '>=', record.date_from))
            if record.date_to:
                domain.append(('date_order', '<=', record.date_to))
            
            # Find all confirmed sale orders in the date range
            sale_orders = self.env['sale.order'].search(domain)
            
            # Calculate total quantity from all order lines
            total_qty = sum(
                line.product_uom_qty 
                for order in sale_orders 
                for line in order.order_line
            )
            
            record.target_achieved = total_qty
    
    def action_open_form(self):
        """Open the form view for this record"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'target.tracking',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('target_tracking.view_target_tracking_form').id,
            'target': 'current',
        }
    
    def action_open_state_list(self):
        """Open list view filtered by this record's state and grouped by district"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Target Tracking - {self.state_id.name}',
            'res_model': 'target.tracking',
            'view_mode': 'list,form',
            'domain': [('state_id', '=', self.state_id.id)],
            'context': {'group_by': 'district', 'default_state_id': self.state_id.id},
            'target': 'current',
        }
    
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Override search to handle date range filtering with overlap logic"""
        _logger.info(f"Target Tracking search - Original args: {args}")
        new_args = []
        i = 0
        
        while i < len(args):
            arg = args[i]
            
            # Handle domain operators (&, |, !)
            if isinstance(arg, str) and arg in ('&', '|', '!'):
                new_args.append(arg)
                i += 1
                continue
            
            if isinstance(arg, (list, tuple)) and len(arg) == 3:
                field, operator, value = arg
                
                # Intercept date_from filters and convert to overlap logic
                if field == 'date_from' and operator in ('>=', '<=', '>', '<', '='):
                    # Date range overlap logic:
                    # Show records where target period overlaps with selected range
                    if operator == '>=':
                        # Selected start date - show records that end on or after this date
                        # (target period ends during or after the selected start date)
                        new_args.append('|')
                        new_args.append(('date_to', '=', False))
                        new_args.append(('date_to', '>=', value))
                    elif operator == '<=':
                        # Selected end date - show records that start on or before this date
                        # (target period starts during or before the selected end date)
                        new_args.append('|')
                        new_args.append(('date_from', '=', False))
                        new_args.append(('date_from', '<=', value))
                    else:
                        # For other operators, keep original behavior
                        new_args.append(arg)
                else:
                    new_args.append(arg)
            else:
                new_args.append(arg)
            
            i += 1
        
        _logger.info(f"Target Tracking search - Transformed args: {new_args}")
        
        # Handle count parameter correctly
        if count:
            return super().search_count(new_args)
        else:
            return super().search(new_args, offset=offset, limit=limit, order=order)

