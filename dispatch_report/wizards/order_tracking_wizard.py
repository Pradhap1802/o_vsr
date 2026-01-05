from odoo import models, fields

class OrderTrackingWizard(models.TransientModel):
    _name = 'order.tracking.wizard'
    _description = 'Order Tracking Report Wizard'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sale', 'Sales Order'),
        ('done', 'Locked')
    ])

    def action_print_report(self):
        return self.env.ref(
            'dispatch_report.action_order_tracking_report'
        ).report_action(self)
