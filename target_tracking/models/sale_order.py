from odoo import models, api, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    user_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        domain="[('user_id', '=', user_id)]"
    )
    
    @api.onchange('user_id')
    def _onchange_user_id_filter_partners(self):
        """Filter partner_id based on selected salesperson"""
        if self.user_id:
            return {'domain': {'partner_id': [('user_id', '=', self.user_id.id)]}}
        else:
            # If no salesperson selected, show all customers
            return {'domain': {'partner_id': [('customer_rank', '>', 0)]}}

    def action_confirm(self):
        """Override action_confirm to update target tracking when order is confirmed"""
        # Call the original action_confirm method
        result = super(SaleOrder, self).action_confirm()
        
        # Update target tracking for each confirmed order
        for order in self:
            # Calculate total quantity from all order lines
            total_qty = sum(line.product_uom_qty for line in order.order_line)
            
            # Get the order date
            order_date = order.date_order.date() if order.date_order else False
            
            if not order_date:
                continue
            
            # Find target tracking records for this customer where order date falls in range
            domain = [('partner_id', '=', order.partner_id.id)]
            
            # Build domain to find matching date ranges
            # Match if: (no date_from OR order_date >= date_from) AND (no date_to OR order_date <= date_to)
            target_trackings = self.env['target.tracking'].search(domain)
            
            matching_records = target_trackings.filtered(
                lambda t: (not t.date_from or order_date >= t.date_from) and 
                         (not t.date_to or order_date <= t.date_to)
            )
            
            if matching_records:
                # Update all matching records (there could be overlapping date ranges)
                for target_tracking in matching_records:
                    target_tracking.target_achieved += total_qty
            else:
                # No matching date range found - optionally create a record without dates
                # or skip (current behavior: skip)
                pass
        
        return result
