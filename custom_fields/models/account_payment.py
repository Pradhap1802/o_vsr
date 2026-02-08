from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    x_studio_tally_receipt_no = fields.Char(
        string='Tally Receipt No.',
        help='Tally payment receipt reference number'
    )
