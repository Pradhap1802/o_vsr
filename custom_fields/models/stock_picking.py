from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_studio_delivery_ref_no = fields.Char(
        string='Delivery Ref No.',
        help='Tally delivery reference number'
    )
    
    x_studio_receipt_ref_no = fields.Char(
        string='Receipt Ref No.',
        help='Tally receipt reference number'
    )
