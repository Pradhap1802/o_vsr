from odoo import models, fields, api
from datetime import date

class StockStatementWizard(models.TransientModel):
    _name = 'vsr.stock.statement.wizard'
    _description = 'Stock Statement Report Wizard'

    date_start = fields.Datetime(string='Start Date', required=True, default=lambda self: fields.Datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0))
    date_end = fields.Datetime(string='End Date', required=True, default=fields.Datetime.now)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    category_ids = fields.Many2many('product.category', string='Categories', default=lambda self: self.env['product.category'].search([]))

    def action_print_report(self):
        data = {
            'date_start': self.date_start,
            'date_end': self.date_end,
            'company_id': self.company_id.id,
            'category_ids': self.category_ids.ids,
        }
        return self.env.ref('vsr_changes.action_report_stock_statement').report_action(self, data=data)
