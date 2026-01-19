from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PlanningSheetWizard(models.TransientModel):
    _name = 'planning.sheet.wizard'
    _description = 'Planning Sheet Report Wizard'

    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)

    def action_print_report(self):
        """
        Creates a temporary planning sheet, loads data from sales, 
        and returns the report action.
        """
        self.ensure_one()
        
        # Create the sheet
        sheet = self.env['planning.sheet'].create({
            'date': self.date,
            'name': f'Planning Sheet - {self.date}'
        })
        
        # Load data from sales orders (using the logic we already verified)
        # We catch potential errors (like no orders found) to avoid blocking the user nicely?
        # The existing method raises UserError if no orders found, which works fine (shows popup).
        sheet.action_load_from_sales()
        
        # Return the report action
        return self.env.ref('vsr_changes.action_report_planning_sheet').report_action(sheet)


class PlanningSheet(models.TransientModel):
    _name = 'planning.sheet'
    _description = 'Daily Packing & Dispatch Report Data'
    
    name = fields.Char(string='Reference', default='New')
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    line_ids = fields.One2many('planning.sheet.line', 'sheet_id', string='Planning Lines')
    notes = fields.Text(string='Notes')
    
    def action_load_from_sales(self):
        """Load planning data from confirmed sale orders for the selected date"""
        self.ensure_one()
        
        # Convert Date to Datetime range for search
        from datetime import datetime, time
        start_date = datetime.combine(self.date, time.min)
        end_date = datetime.combine(self.date, time.max)
        
        # Find sale orders with commitment date within the selected date
        sale_orders = self.env['sale.order'].search([
            ('state', 'in', ['sale', 'done']),
            ('commitment_date', '>=', start_date),
            ('commitment_date', '<=', end_date),
        ])
        
        if not sale_orders:
             raise UserError(_('No confirmed sales orders found with Delivery Date (Commitment Date) on %s.\n\nPlease check the "Delivery Date" on your Sales Orders.') % self.date)

        # Collect data: {(product, city): qty}
        planning_data = {}
        
        for order in sale_orders:
            # Get customer city
            city = order.partner_id.city or order.partner_shipping_id.city
            if not city:
                city = 'Unknown'
            
            # Process order lines
            for line in order.order_line:
                if line.display_type: continue # Skip section/notes
                if line.product_id.type in ['product', 'consu']:  # Allow Storable and Consumable
                    key = (line.product_id, city)
                    if key not in planning_data:
                        planning_data[key] = 0.0
                    planning_data[key] += line.product_uom_qty
        
        if not planning_data:
            raise UserError(_('Confirmed sales orders were found for %s, but they do not contain any Storable or Consumable products to plan.') % self.date)

        # Create planning lines
        sequence = 10
        for (product, city), qty in planning_data.items():
            self.env['planning.sheet.line'].create({
                'sheet_id': self.id,
                'product_id': product.id,
                'city': city,
                'quantity': qty,
                'stocks_in_kgs': product.qty_available,
                'sequence': sequence,
            })
            sequence += 10

class PlanningSheetLine(models.TransientModel):
    _name = 'planning.sheet.line'
    _description = 'Planning Sheet Line'
    _order = 'product_id, city, sequence'

    sheet_id = fields.Many2one('planning.sheet', string='Planning Sheet', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    
    product_id = fields.Many2one('product.product', string='Product', required=True)
    city = fields.Char(string='City/Location', required=True)
    quantity = fields.Float(string='Quantity', default=0.0)
    stocks_in_kgs = fields.Float(string='Stocks in KGS')
    
    # Computed fields
    req_qty_in_kgs = fields.Float(string='Req Qty in KGS', compute='_compute_req_qty', store=True)
    
    @api.depends('quantity', 'product_id')
    def _compute_req_qty(self):
        for line in self:
            if line.product_id and line.product_id.weight:
                line.req_qty_in_kgs = line.quantity * line.product_id.weight
            else:
                # Try to extract weight from product name
                weight = self._extract_weight_from_name(line.product_id.name if line.product_id else '')
                line.req_qty_in_kgs = line.quantity * weight
    
    def _extract_weight_from_name(self, name):
        """Extract weight from product name like 'MANGO PICKLE AS 5 KG'"""
        import re
        if not name:
            return 0.0
        
        # Look for patterns like "5 KG", "2.5 Kg", etc.
        match = re.search(r'(\d+\.?\d*)\s*[Kk][Gg]', name)
        if match:
            return float(match.group(1))
        return 0.0
