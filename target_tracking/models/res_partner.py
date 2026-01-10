from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    district = fields.Char(
        string='District',
        help='District or region for grouping customers'
    )

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
