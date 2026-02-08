from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_studio_tally_sales_no = fields.Char(
        string='Tally Sales No.',
        help='Tally sales invoice reference number'
    )
    
    x_studio_tally_purchase_no = fields.Char(
        string='Tally Purchase No.',
        help='Tally purchase invoice reference number'
    )
