from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_studio_tally_order_no = fields.Char(
        string='Tally Order No.',
        help='Tally order reference number'
    )
