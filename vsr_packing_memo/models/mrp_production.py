# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    production_type = fields.Selection(
        [
            ('packing_memo', 'Packing Memo'),
            ('production_memo', 'Production Memo'),
        ],
        string='Production Type',
        default='packing_memo',
        required=True,
        help='Type of production: Packing Memo or Production Memo'
    )

    no_of_lots = fields.Integer(
        string='No of Lots',
        default=1,
        help='Number of lots involved in this production'
    )

    memo_no = fields.Integer(
        string='Memo No',
        copy=False,
        readonly=True,
        help='Sequence number for this product production'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Only generate Memo No for Packing Memo type
            if vals.get('production_type', 'packing_memo') == 'packing_memo' and vals.get('product_id'):
                # Find the last sequence number for this product
                last_record = self.search([
                    ('product_id', '=', vals['product_id']),
                    ('memo_no', '!=', False),
                    ('production_type', '=', 'packing_memo')
                ], order='memo_no desc', limit=1)
                vals['memo_no'] = (last_record.memo_no or 0) + 1
        return super().create(vals_list)

    qty_per_lot = fields.Float(
        string='Qty per Lot',
        default=1.0,
        digits='Product Unit of Measure',
        help='Internal field to track quantity per lot for scaling'
    )

    @api.onchange('product_qty')
    def _onchange_product_qty_track_base(self):
        """Update base qty per lot when total qty is manually changed"""
        for production in self:
            if production.no_of_lots >= 1:
                production.qty_per_lot = production.product_qty / production.no_of_lots
            else:
                production.qty_per_lot = production.product_qty

    @api.onchange('no_of_lots')
    def _onchange_no_of_lots(self):
        """Update product_qty based on number of lots"""
        for production in self:
            if production.no_of_lots < 1:
                production.no_of_lots = 1
            
            # Update total quantity
            production.product_qty = production.qty_per_lot * production.no_of_lots
            
            # Retrieve the appropriate onchange method for updating components
            if hasattr(production, '_onchange_product_qty'):
                production._onchange_product_qty()
            elif hasattr(production, 'onchange_product_qty'):
                production.onchange_product_qty()

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
