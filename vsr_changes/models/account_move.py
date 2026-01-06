from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    partner_division = fields.Char(
        string='Division',
        related='partner_id.division',
        store=True,
        readonly=True,
        help='Division from partner for grouping invoices'
    )

    vsr_vehicle_number = fields.Char(
        string='Vehicle Number', 
        compute='_compute_vsr_vehicle_number', 
        store=True, 
        readonly=False,
        help='Vehicle number mapped from eWaybill or manually entered'
    )
    
    delivery_number = fields.Char(
        string='Dispatch Number', 
        compute='_compute_delivery_number', 
        store=True
    )
    
    destination = fields.Char(string='Destination')

    @api.depends('l10n_in_vehicle_no')
    def _compute_vsr_vehicle_number(self):
        for move in self:
            # Check if l10n_in_vehicle_no exists (module installed)
            if hasattr(move, 'l10n_in_vehicle_no') and move.l10n_in_vehicle_no:
                move.vsr_vehicle_number = move.l10n_in_vehicle_no
            elif not move.vsr_vehicle_number:
                move.vsr_vehicle_number = False

    @api.depends('invoice_line_ids.sale_line_ids.order_id.picking_ids', 'invoice_line_ids.sale_line_ids.order_id.picking_ids.state')
    def _compute_delivery_number(self):
        for move in self:
            # Use picking_type_id.code which is more reliable than picking_type_code related field
            delivery_ids = move.invoice_line_ids.sale_line_ids.order_id.picking_ids.filtered(
                lambda p: p.state == 'done' and p.picking_type_id.code == 'outgoing'
            )
            if delivery_ids:
                move.delivery_number = ", ".join(delivery_ids.mapped('name'))
            else:
                move.delivery_number = ""


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    pieces_per_case = fields.Integer(
        string='Pieces', 
        related='product_id.pieces_per_case', 
        readonly=False, 
        store=True
    )
    price_per_piece = fields.Float(
        string='Price/Piece', 
        related='product_id.price_per_piece', 
        digits='Product Price', 
        readonly=False, 
        store=True
    )
