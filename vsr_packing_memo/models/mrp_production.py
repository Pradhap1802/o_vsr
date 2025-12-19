# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    packing_memo_remarks = fields.Text(
        string='Packing Memo Remarks',
        help='Additional remarks for the packing memo report'
    )

    @api.depends('move_raw_ids', 'move_raw_ids.quantity')
    def _compute_total_raw_materials_issued(self):
        """Compute total quantity of raw materials issued/consumed"""
        for production in self:
            total_issued = sum(production.move_raw_ids.filtered(
                lambda m: m.state != 'cancel'
            ).mapped('quantity'))
            production.total_raw_materials_issued = total_issued

    total_raw_materials_issued = fields.Float(
        string='Total Raw Materials Issued',
        compute='_compute_total_raw_materials_issued',
        help='Total quantity of raw materials consumed in this manufacturing order'
    )

    @api.depends('scrap_ids', 'scrap_ids.scrap_qty')
    def _compute_total_wastage(self):
        """Compute total wastage/defectives from scrap records"""
        for production in self:
            total_wastage = sum(production.scrap_ids.filtered(
                lambda s: s.state == 'done'
            ).mapped('scrap_qty'))
            production.total_wastage = total_wastage

    total_wastage = fields.Float(
        string='Total Wastage/Defectives',
        compute='_compute_total_wastage',
        help='Total quantity scrapped/wasted in this manufacturing order'
    )
