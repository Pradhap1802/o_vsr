from odoo import models, fields, api

class ColdStorage(models.Model):
    _name = 'cold.storage'
    _description = 'Cold Storage Statement'
    _order = 'date desc, id desc'
    _rec_name = 'date'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # partner_id removed as requested

    date = fields.Date(string='Statement Date', default=fields.Date.context_today)
    
    # Stock Lines
    stock_line_ids = fields.One2many('cold.storage.stock.line', 'cold_storage_id', string='Stock Rent Lines')
    
    # Payment Lines
    payment_line_ids = fields.One2many('cold.storage.payment.line', 'cold_storage_id', string='Payment Release')
    
    # Computations
    total_rent_amount = fields.Float(string='Total Rent Amount', compute='_compute_totals', store=True)
    total_paid_amount = fields.Float(string='Total Paid Amount', compute='_compute_totals', store=True)
    balance_amount = fields.Float(string='Balance Amount', compute='_compute_totals', store=True)
    
    @api.depends('stock_line_ids.amount', 'payment_line_ids.amount_paid')
    def _compute_totals(self):
        for record in self:
            record.total_rent_amount = sum(record.stock_line_ids.mapped('amount'))
            record.total_paid_amount = sum(record.payment_line_ids.mapped('amount_paid'))
            record.balance_amount = record.total_rent_amount - record.total_paid_amount


class ColdStorageStockLine(models.Model):
    _name = 'cold.storage.stock.line'
    _description = 'Cold Storage Stock Line'

    cold_storage_id = fields.Many2one('cold.storage', string='Cold Storage Statement', ondelete='cascade')
    
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    card_no = fields.Char(string='Card No')
    product_id = fields.Many2one('product.product', string='Variety')
    bags = fields.Integer(string='Bags')
    weight = fields.Float(string='Weight')
    price_per_kg = fields.Float(string='Per Kg')
    month_multiplier = fields.Float(string='Month x2')
    yearly_amount = fields.Float(string='Yearly', compute='_compute_amounts', store=True, readonly=False)
    
    amount = fields.Float(string='Amount', compute='_compute_amounts', store=True, readonly=False)

    @api.depends('weight', 'price_per_kg', 'month_multiplier')
    def _compute_amounts(self):
        for line in self:
            # Yearly Amount = Weight * Per Kg * 12
            yearly = line.weight * line.price_per_kg * 12
            line.yearly_amount = yearly
            
            # Extra Amount = Month Multiplier
            extra = line.month_multiplier
            
            # Total Amount = Yearly Amount + Extra Amount
            line.amount = yearly + extra


class ColdStoragePaymentLine(models.Model):
    _name = 'cold.storage.payment.line'
    _description = 'Cold Storage Payment Line'

    cold_storage_id = fields.Many2one('cold.storage', string='Cold Storage Statement', ondelete='cascade')
    
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    bank_name = fields.Char(string='Payment Release Of Bank Account')
    amount_paid = fields.Float(string='Amount Of Paid')
