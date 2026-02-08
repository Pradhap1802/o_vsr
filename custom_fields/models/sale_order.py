from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_studio_tally_order_no = fields.Char(
        string='Tally Order No.',
        help='Tally order reference number'
    )
