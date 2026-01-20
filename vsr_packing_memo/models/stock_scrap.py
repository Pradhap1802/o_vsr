# -*- coding: utf-8 -*-
from odoo import fields, models


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    scrap_remarks = fields.Text(
        string='Remarks',
        help='Additional remarks for the scrap/wastage'
    )
    
    lot_no = fields.Char(string='Lot Number')
    production_type = fields.Selection(related='production_id.production_type', string='Production Type')
