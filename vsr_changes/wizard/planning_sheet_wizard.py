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
    
    # Computed fields
    stocks_in_kgs = fields.Char(string='Stocks in KGS', compute='_compute_stocks_in_kgs', store=True)
    req_qty_in_kgs = fields.Float(string='Req Qty in KGS', compute='_compute_req_qty', store=True)
    
    @api.depends('product_id')
    def _compute_stocks_in_kgs(self):
        """Extract weight with unit from product name and display it in Stocks in KGS column"""
        for line in self:
            if not line.product_id:
                line.stocks_in_kgs = ''
                continue
            
            # Extract weight with unit from product name
            line.stocks_in_kgs = self._extract_weight_with_unit(line.product_id.name)
    
    def _extract_weight_with_unit(self, name):
        """
        Extract weight with unit from product name.
        Returns: string like '500 G', '1 KG', '2.5 KG', etc.
        """
        import re
        if not name:
            return ''
        
        name_upper = name.upper()
        
        # Define weight patterns to extract
        weight_patterns = [
            # KG patterns
            (r'5\s*KG', '5 KG'),
            (r'2\.5\s*KG', '2.5 KG'),
            (r'1\s*KG', '1 KG'),
            # Gram patterns
            (r'500\s*G', '500 G'),
            (r'300\s*G', '300 G'),
            (r'200\s*G', '200 G'),
            (r'100\s*G', '100 G'),
            (r'60\s*G', '60 G'),
            (r'30\s*G', '30 G'),
            (r'7\s*G', '7 G'),
        ]
        
        # Try to match each pattern
        for pattern, display_text in weight_patterns:
            if re.search(pattern, name_upper):
                return display_text
        
        # Fallback: try to extract any KG value
        kg_match = re.search(r'(\d+\.?\d*)\s*KG', name_upper)
        if kg_match:
            return f"{kg_match.group(1)} KG"
        
        # Fallback: try to extract any G value
        g_match = re.search(r'(\d+\.?\d*)\s*G', name_upper)
        if g_match:
            return f"{g_match.group(1)} G"
        
        return ''
    
    
    
    @api.depends('quantity', 'product_id')
    def _compute_req_qty(self):
        for line in self:
            if not line.product_id or not line.quantity:
                line.req_qty_in_kgs = 0.0
                continue
            
            # Extract weight and pieces per case from product name
            weight_kg, pieces_per_case = self._extract_weight_and_pieces(line.product_id.name)
            
            # Calculate: Total Qty in Case × Weight in KG × Pieces per Case
            line.req_qty_in_kgs = line.quantity * weight_kg * pieces_per_case
    
    def _extract_weight_and_pieces(self, name):
        """
        Extract weight from product name and return corresponding pieces per case.
        Returns: (weight_in_kg, pieces_per_case)
        """
        import re
        if not name:
            return 0.0, 0
        
        name_upper = name.upper()
        
        # Define weight patterns and their corresponding pieces per case
        weight_mapping = [
            # KG patterns
            (r'5\s*KG', 5.0, 4),
            (r'2\.5\s*KG', 2.5, 6),
            (r'1\s*KG', 1.0, 12),
            # Gram patterns
            (r'500\s*G', 0.5, 24),
            (r'300\s*G', 0.3, 40),
            (r'200\s*G', 0.2, 60),
            (r'100\s*G', 0.1, 90),
            (r'60\s*G', 0.06, 160),
            (r'30\s*G', 0.03, 40),
            (r'7\s*G', 0.007, 1500),
        ]
        
        # Try to match each pattern
        for pattern, weight_kg, pieces in weight_mapping:
            if re.search(pattern, name_upper):
                return weight_kg, pieces
        
        # Fallback: try to extract any KG value
        kg_match = re.search(r'(\d+\.?\d*)\s*KG', name_upper)
        if kg_match:
            return float(kg_match.group(1)), 1
        
        # Fallback: try to extract any G value
        g_match = re.search(r'(\d+\.?\d*)\s*G', name_upper)
        if g_match:
            return float(g_match.group(1)) / 1000.0, 1
        
        return 0.0, 0
