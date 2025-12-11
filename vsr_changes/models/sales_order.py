from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class SaleOrderVSR(models.Model):
    _inherit = 'sale.order'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to check for pending/due payments when creating new sales order"""
        records = super().create(vals_list)
        
        for order in records:
            # Check if customer has pending or due payments from previous orders
            order._check_and_warn_pending_payments()
        
        return records

    def action_confirm(self):
        """Override action_confirm to check for pending/due payments"""
        for order in self:
            # Check if customer has pending or due payments
            order._check_pending_payments()
        
        return super().action_confirm()

    def _check_and_warn_pending_payments(self):
        """Check for pending or due invoices and show warning popup"""
        self.ensure_one()
        
        if not self.partner_id:
            return
        
        try:
            # Search for previous orders with unpaid invoices for this customer
            unpaid_invoices = self.env['account.move'].search([
                ('partner_id', '=', self.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('payment_state', '=', 'not_paid'),
                ('state', '=', 'posted'),
            ])
            
            overdue_invoices = self.env['account.move'].search([
                ('partner_id', '=', self.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('payment_state', '=', 'not_paid'),
                ('state', '=', 'posted'),
                ('invoice_date_due', '<', fields.Date.today()),
            ])
            
            # Get related sales orders from invoices
            related_orders = self.env['sale.order'].search([
                ('partner_id', '=', self.partner_id.id),
                ('invoice_ids', 'in', unpaid_invoices.ids + overdue_invoices.ids),
            ])
            
            # Build warning message
            warning_message = ""
            
            if overdue_invoices:
                overdue_count = len(overdue_invoices)
                overdue_total = sum(overdue_invoices.mapped('amount_residual'))
                order_numbers = ', '.join(related_orders.mapped('name'))
                warning_message += f"⚠️ OVERDUE ALERT:\n"
                warning_message += f"Customer has {overdue_count} overdue invoice(s) totaling {overdue_total:.2f}\n"
                warning_message += f"Related Sales Orders: {order_numbers or 'N/A'}\n\n"
            
            if unpaid_invoices and not overdue_invoices:
                unpaid_count = len(unpaid_invoices)
                unpaid_total = sum(unpaid_invoices.mapped('amount_residual'))
                order_numbers = ', '.join(related_orders.mapped('name'))
                warning_message += f"⚠️ PAYMENT PENDING:\n"
                warning_message += f"{self.partner_id.name} has {unpaid_count} pending invoice(s) totaling {unpaid_total:.2f}\n"
                warning_message += f"Related Sales Orders: {order_numbers or 'N/A'}\n\n"
            
            # Create a note in the order for record keeping and raise alert
            if warning_message:
                self.message_post(body=f"<strong style='color: red;'>{warning_message}</strong>")
                
                # Raise a UserError with action button
                raise UserError(
                    f"⚠️ PAYMENT Pending ⚠️\n\n"
                    f"Customer: {self.partner_id.name}\n\n"
                    f"{warning_message}\n"
                    f"Please verify payment status before proceeding."
                )
        
        except UserError:
            raise
        except Exception as e:
            # Log the error but don't block the creation
            _logger.warning(f'Error checking payments for {self.partner_id.name}: {str(e)}')

    def _check_pending_payments(self):
        """Check for pending or due invoices for the customer"""
        self.ensure_one()
        
        if not self.partner_id:
            return
        
        try:
            # Search for pending or overdue invoices for this customer
            pending_invoices = self.env['account.move'].search([
                ('partner_id', '=', self.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('state', '=', 'posted'),
            ])
            
            overdue_invoices = self.env['account.move'].search([
                ('partner_id', '=', self.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('payment_state', '=', 'not_paid'),
                ('state', '=', 'posted'),
                ('invoice_date_due', '<', fields.Date.today()),
            ])
            
            # Generate alert messages
            alert_message = ""
            
            if pending_invoices:
                pending_count = len(pending_invoices)
                pending_total = sum(pending_invoices.mapped('amount_residual'))
                alert_message += f"\n⚠️ WARNING: Customer has {pending_count} pending invoice(s) totaling ${pending_total:.2f}"
            
            if overdue_invoices:
                overdue_count = len(overdue_invoices)
                overdue_total = sum(overdue_invoices.mapped('amount_residual'))
                alert_message += f"\n⚠️ ALERT: Customer has {overdue_count} overdue invoice(s) totaling ${overdue_total:.2f}"
            
            # Create a note in the order for record keeping
            if alert_message:
                self.message_post(body=f"<strong>Payment Alert:</strong>{alert_message}")
        
        except Exception as e:
            # Log the error but don't block the confirmation
            _logger.warning(f'Error checking payments during confirmation: {str(e)}')
            _logger.warning(f'Error checking payments during confirmation: {str(e)}')

