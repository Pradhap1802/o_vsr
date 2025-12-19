from odoo import models, fields, api

class StockMoveVSR(models.Model):
    _inherit = 'stock.move'

    rate = fields.Float(
        string='Rate',
        digits='Product Price',
        compute='_compute_rate_and_taxes',
        store=True,
        readonly=False,
        help='Unit price from purchase order'
    )
    
    vsr_tax_ids = fields.Many2many(
        'account.tax',
        'stock_move_vsr_tax_rel',
        'move_id',
        'tax_id',
        string='Taxes',
        compute='_compute_rate_and_taxes',
        store=True,
        readonly=False,
        help='Taxes from purchase order'
    )
    
    subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help='Rate * Quantity'
    )
    
    tax_amount = fields.Monetary(
        string='Tax Amount',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help='Computed tax amount'
    )
    
    total = fields.Monetary(
        string='Total',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help='Subtotal + Tax Amount'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True
    )

    @api.depends('purchase_line_id', 'purchase_line_id.price_unit', 'purchase_line_id.taxes_id')
    def _compute_rate_and_taxes(self):
        for move in self:
            if move.purchase_line_id:
                move.rate = move.purchase_line_id.price_unit
                move.vsr_tax_ids = move.purchase_line_id.taxes_id
            elif not move.rate:
                move.rate = 0.0
                if not move.vsr_tax_ids:
                    move.vsr_tax_ids = False

    @api.depends('rate', 'product_uom_qty', 'vsr_tax_ids')
    def _compute_totals(self):
        for move in self:
            move.subtotal = move.rate * move.product_uom_qty
            
            if move.vsr_tax_ids and move.subtotal:
                tax_results = move.vsr_tax_ids.compute_all(
                    move.rate,
                    currency=move.currency_id,
                    quantity=move.product_uom_qty,
                    product=move.product_id,
                    partner=move.picking_id.partner_id if move.picking_id else None
                )
                move.tax_amount = sum(tax['amount'] for tax in tax_results['taxes'])
                move.total = tax_results['total_included']
            else:
                move.tax_amount = 0.0
                move.total = move.subtotal
