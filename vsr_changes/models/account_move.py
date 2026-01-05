from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    partner_division = fields.Char(
        string='Division',
        related='partner_id.division',
        store=True,
        readonly=True,
        help='Division from partner for grouping invoices'
    )
