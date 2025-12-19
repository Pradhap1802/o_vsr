from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_type = fields.Selection([
        ('vendor', 'Vendor'),
        ('customer', 'Customer'),
    ], string='Partner Type',
       help='Select whether this partner is a Vendor or Customer')

    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        """Update supplier_rank and customer_rank based on partner_type"""
        if self.partner_type == 'vendor':
            # Set as supplier only - will show in Purchase
            self.supplier_rank = 1
            self.customer_rank = 0
        elif self.partner_type == 'customer':
            # Set as customer only - will show in Sales
            self.customer_rank = 1
            self.supplier_rank = 0

    @api.model_create_multi
    def create(self, vals_list):
        """Set supplier_rank and customer_rank on creation based on partner_type"""
        partners = super(ResPartner, self).create(vals_list)
        for partner in partners:
            if partner.partner_type:
                # Apply the partner_type logic
                if partner.partner_type == 'vendor':
                    partner.supplier_rank = 1
                    partner.customer_rank = 0
                elif partner.partner_type == 'customer':
                    partner.customer_rank = 1
                    partner.supplier_rank = 0
        return partners

    def write(self, vals):
        """Update supplier_rank and customer_rank when partner_type changes"""
        # If partner_type is being changed, update the ranks in vals
        if 'partner_type' in vals:
            if vals['partner_type'] == 'vendor':
                vals['supplier_rank'] = 1
                vals['customer_rank'] = 0
            elif vals['partner_type'] == 'customer':
                vals['customer_rank'] = 1
                vals['supplier_rank'] = 0
        
        result = super(ResPartner, self).write(vals)
        return result