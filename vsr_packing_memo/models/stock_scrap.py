# -*- coding: utf-8 -*-
from odoo import fields, models


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    scrap_remarks = fields.Text(
        string='Remarks',
        help='Additional remarks for the scrap/wastage'
    )
