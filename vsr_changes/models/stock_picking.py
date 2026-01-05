from odoo import models, fields, api

class StockPickingVSR(models.Model):
    _inherit = 'stock.picking'
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True
    )
    
    amount_untaxed = fields.Monetary(
        string='Untaxed Amount',
        compute='_compute_amounts',
        currency_field='currency_id',
        help='Sum of all move subtotals'
    )
    
    amount_tax = fields.Monetary(
        string='Taxes',
        compute='_compute_amounts',
        currency_field='currency_id',
        help='Sum of all move tax amounts'
    )
    
    amount_total = fields.Monetary(
        string='Total',
        compute='_compute_amounts',
        currency_field='currency_id',
        help='Sum of all move totals (including taxes)'
    )
    
    @api.depends('move_ids_without_package.subtotal', 'move_ids_without_package.tax_amount', 'move_ids_without_package.total')
    def _compute_amounts(self):
        for picking in self:
            amount_untaxed = sum(move.subtotal for move in picking.move_ids_without_package)
            amount_tax = sum(move.tax_amount for move in picking.move_ids_without_package)
            amount_total = sum(move.total for move in picking.move_ids_without_package)
            
            picking.amount_untaxed = amount_untaxed
            picking.amount_tax = amount_tax
            picking.amount_total = amount_total
    
    def get_tax_details(self):
        """Get tax breakdown by tax name"""
        self.ensure_one()
        tax_details = {}
        
        for move in self.move_ids_without_package:
            if move.vsr_tax_ids and move.subtotal:
                tax_results = move.vsr_tax_ids.compute_all(
                    move.rate,
                    currency=self.currency_id,
                    quantity=move.product_uom_qty,
                    product=move.product_id,
                    partner=self.partner_id
                )
                for tax in tax_results['taxes']:
                    tax_name = tax['name']
                    tax_amount = tax['amount']
                    if tax_name in tax_details:
                        tax_details[tax_name] += tax_amount
                    else:
                        tax_details[tax_name] = tax_amount
        
        return tax_details
class stock_picking(models.Model):
    _inherit = 'stock.picking'

    state = fields.Selection(selection_add=[     
        ('advance_payment', 'Advance Payment'),
        ('line_setting', 'Line Setting'),
        ('payment_balance', 'payment Balance'),

        
        
      
    ],
    force_store='1',)

    dispatch_stage = fields.Selection(
        selection=[
            ('advance_payment', 'Advance Payment'),
            ('line_setting', 'Line Setting'),
            ('payment_balance', 'Payment Balance'),
        ],
        string="Dispatch Status",
        tracking=True,
        copy=False
    )




    def write(self, vals):
        res = super().write(vals)

        if 'dispatch_stage' in vals:
            for picking in self:
                if picking.dispatch_stage == 'advance_payment':
                    picking.state = 'advance_payment'

                elif picking.dispatch_stage == 'line_setting':
                    picking.state = 'line_setting'

                elif picking.dispatch_stage == 'payment_balance':
                    picking.state = 'payment_balance'
                    

        return res
