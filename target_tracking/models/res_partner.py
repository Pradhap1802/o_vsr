from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    district = fields.Char(
        string='District',
        help='District or region for grouping customers'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Create target tracking record when a customer is created"""
        partners = super(ResPartner, self).create(vals_list)
        
        # Create target tracking records for customers
        tracking_vals = []
        for partner in partners:
            # Check if this is a customer (either customer_rank > 0 or partner_type = 'customer')
            is_customer = partner.customer_rank > 0
            if hasattr(partner, 'partner_type') and partner.partner_type == 'customer':
                is_customer = True
            
            if is_customer:
                tracking_vals.append({
                    'partner_id': partner.id,
                    'super_stockiest_id': partner.id,  # Automatically set to same customer
                })
        
        if tracking_vals:
            self.env['target.tracking'].create(tracking_vals)
        
        return partners

    def write(self, vals):
        """Update target tracking records when partner is updated"""
        result = super(ResPartner, self).write(vals)
        
        # Update related target tracking records if district, name, phone, or parent changes
        if any(field in vals for field in ['district', 'name', 'phone', 'parent_id']):
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
