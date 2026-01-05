from odoo import models, fields, api

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