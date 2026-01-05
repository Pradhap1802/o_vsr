class ReportOrderTracking(models.AbstractModel):
    _name = 'report.your_module.report_order_tracking'

    def _get_report_values(self, docids, data=None):
        wizard = self.env['order.tracking.wizard'].browse(docids)

        domain = [
            ('date_order', '>=', wizard.date_from),
            ('date_order', '<=', wizard.date_to),
        ]
        if wizard.state:
            domain.append(('state', '=', wizard.state))

        orders = self.env['sale.order'].search(domain, order='date_order asc')

        return {
            'docs': orders,
            'wizard': wizard,
        }
