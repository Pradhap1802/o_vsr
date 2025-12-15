from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrderVSR(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _onchange_partner_id_payment_warning(self):
        """
        When the partner is changed on the sales order, check for pending
        or overdue payments and display a warning popup if any are found.
        """
        if not self.partner_id:
            return

        partner = self.partner_id
        
        unpaid_invoices = self.env['account.move'].search([
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_invoice'),
            ('payment_state', '=', 'not_paid'),
            ('state', '=', 'posted'),
        ])
        
        overdue_invoices = unpaid_invoices.filtered(lambda inv: inv.invoice_date_due and inv.invoice_date_due < fields.Date.today())

        if not unpaid_invoices and not overdue_invoices:
            return

        # Build warning message
        warning_parts = []

        # Get related sales orders for all unpaid invoices
        all_related_orders = self.env['sale.order'].search([
            ('partner_id', '=', partner.id),
            ('invoice_ids', 'in', unpaid_invoices.ids),
        ]).mapped('name')
        
        order_numbers_str = ', '.join(all_related_orders) if all_related_orders else 'N/A'

        if overdue_invoices:
            overdue_count = len(overdue_invoices)
            overdue_total = sum(overdue_invoices.mapped('amount_residual'))
            warning_parts.append(f"- {overdue_count} overdue invoice(s) totaling {overdue_total:.2f}.")
        
        pending_invoices_not_overdue = unpaid_invoices - overdue_invoices
        if pending_invoices_not_overdue:
            pending_count = len(pending_invoices_not_overdue)
            pending_total = sum(pending_invoices_not_overdue.mapped('amount_residual'))
            warning_parts.append(f"- {pending_count} pending (not overdue) invoice(s) totaling {pending_total:.2f}.")
        
        if all_related_orders:
            warning_parts.append(f"\nRelated Sales Orders: {order_numbers_str}")
        
        warning_message = "\n".join(warning_parts)
        
        return {
            'warning': {
                'title': f"Payment Warning: {partner.name}",
                'message': warning_message,
            }
        }

    # The action_confirm check is still useful to have, as it runs if the user confirms an existing order
    # that was created before the partner had pending payments.
    def action_confirm(self):
        """Override action_confirm to log a message about pending/due payments"""
        for order in self:
            # Check if customer has pending or due payments
            order._check_pending_payments()
        
        return super().action_confirm()

    def _check_pending_payments(self):
        """Check for pending or due invoices for the customer and log to chatter."""
        self.ensure_one()
        
        if not self.partner_id:
            return
        
        try:
            pending_invoices = self.env['account.move'].search([
                ('partner_id', '=', self.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('state', '=', 'posted'),
            ])
            
            overdue_invoices = pending_invoices.filtered(lambda inv: inv.invoice_date_due and inv.invoice_date_due < fields.Date.today())
            
            if not pending_invoices and not overdue_invoices:
                return

            alert_parts = []
            
            if overdue_invoices:
                overdue_count = len(overdue_invoices)
                overdue_total = sum(overdue_invoices.mapped('amount_residual'))
                alert_parts.append(f"- {overdue_count} overdue invoice(s) totaling {overdue_total:.2f}.")

            pending_not_overdue = pending_invoices - overdue_invoices
            if pending_not_overdue:
                pending_count = len(pending_not_overdue)
                pending_total = sum(pending_not_overdue.mapped('amount_residual'))
                alert_parts.append(f"- {pending_count} pending invoice(s) totaling {pending_total:.2f}.")
            
            alert_message = "\n".join(alert_parts)
            
            if alert_message:
                self.message_post(body=f"<strong>Payment Confirmation Alert:</strong>\n{alert_message}")
        
        except Exception as e:
            _logger.warning(f'Error checking payments during confirmation: {str(e)}')
