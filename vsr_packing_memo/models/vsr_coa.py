from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

class VsrCoa(models.Model):
    _name = 'vsr.coa'
    _description = 'Certificate of Analysis'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Certificate No', required=True, copy=False, readonly=True, default='New', index=True)
    partner_id = fields.Many2one('res.partner', string='Customer Name & Address')
    date_processing = fields.Date(string='Date of Processing', default=fields.Date.context_today)
    po_number = fields.Char(string='PO Number')
    category = fields.Selection([
        ('finished pickle', 'Finished Pickle'),
        ('brine/salted', 'Brine/Salted')
    ], string='Category', default='finished pickle')
    invoice_no = fields.Char(string='Invoice No.')
    truck_no = fields.Char(string='Truck No.')
    lot_no = fields.Char(string='Lot No/Batch No')
    product_description = fields.Char(string='Product Description')
    dispatch_date = fields.Date(string='Dispatch Date')
    
    exp_date_text = fields.Char(string='Exp Date Text', default='Best Before 10 Months Date Of Packing.')
    variety_of_pickle = fields.Char(string='Variety Of Pickle')

    line_ids = fields.One2many('vsr.coa.line', 'coa_id', string='Analytical Parameters')
    comment = fields.Text(string='Comment')
    
    verified_by = fields.Char(string='Verified & Approved By Name')
    prepared_by = fields.Char(string='Prepared By Name')

    @api.onchange('category')
    def _onchange_category(self):
        if self.category == 'brine/salted':
            self.comment = "Store in Proper Condition at Below 25c room temprature.\n100 % Vegetarian."
            lines = [
                (0, 0, {'parameter': 'Colour', 'uom': '-', 'result': 'Red', 'standard': 'Red', 'test_method': 'MANDATORY'}),
                (0, 0, {'parameter': 'Appearance', 'uom': '-', 'result': 'Mango Pieces & Spices in Oil', 'standard': 'Pieces & Spices in Oil', 'test_method': 'MANDATORY'}),
                (0, 0, {'parameter': 'Flavour', 'uom': '-', 'result': 'Spicy,Sour', 'standard': 'Spicy,Sour', 'test_method': 'MANDATORY'}),
                (0, 0, {'parameter': 'Odour', 'uom': '-', 'result': 'Gravy With Pieces', 'standard': 'Gravy With Pieces', 'test_method': 'MANDATORY'}),
                (0, 0, {'parameter': 'Acidity', 'uom': '%', 'result': 'eg 1', 'standard': 'eg 1-2', 'test_method': 'TITRATION'}),
                (0, 0, {'parameter': 'Salt', 'uom': '%', 'result': 'eg 2', 'standard': 'eg 1-3', 'test_method': 'TITRATION'}),
            ]
            self.line_ids = [(5, 0, 0)] + lines
        elif self.category == 'finished pickle':
             # Default finished pickle lines (as per previous logic, simplistic reset)
            lines = [
                (0, 0, {'parameter': 'ACIDITY', 'uom': '%', 'standard': 'eg (1-2)', 'test_method': 'TITRATION'}),
                (0, 0, {'parameter': 'SALT', 'uom': '%', 'standard': 'eg (1-2)', 'test_method': 'TITRATION'}),
                (0, 0, {'parameter': 'PIECES SIZE', 'uom': 'MM', 'standard': '-', 'test_method': '-'}),
            ]
            self.line_ids = [(5, 0, 0)] + lines
            self.comment = ""

    @api.onchange('date_processing')
    def _onchange_date_processing(self):
        if self.date_processing:
            # Calculate 10 months from date_processing
            exp_date = self.date_processing + relativedelta(months=10)
            self.exp_date_text = f"Best Before {exp_date.strftime('%d.%m.%Y')}"
        else:
            self.exp_date_text = 'Best Before 10 Months Date Of Packing.'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('vsr.coa') or 'New'
        return super().create(vals_list)

    @api.model
    def default_get(self, fields_list):
        res = super(VsrCoa, self).default_get(fields_list)
        # Only populate defaults if creating a fresh record (no category pre-set usually, but default is finished pickle)
        # The onchange handles UI interaction, default_get handles initial load.
        # We can rely on default='finished pickle' and populate based on that.
        if 'line_ids' in fields_list and 'category' not in res: 
             # Assuming default category is finished pickle
             lines = [
                (0, 0, {'parameter': 'ACIDITY', 'uom': '%', 'standard': 'eg (1-2)', 'test_method': 'TITRATION'}),
                (0, 0, {'parameter': 'SALT', 'uom': '%', 'standard': 'eg (1-2)', 'test_method': 'TITRATION'}),
                (0, 0, {'parameter': 'PIECES SIZE', 'uom': 'MM', 'standard': '-', 'test_method': '-'}),
            ]
             res.update({'line_ids': lines})
        return res

class VsrCoaLine(models.Model):
    _name = 'vsr.coa.line'
    _description = 'COA Parameter Line'

    coa_id = fields.Many2one('vsr.coa', string='COA')
    parameter = fields.Char(string='Parameters Tested', required=True)
    uom = fields.Char(string='Unit of Measurement')
    result = fields.Char(string='Result')
    standard = fields.Char(string='Standard (As Per Product Specs)')
    test_method = fields.Char(string='Test Method')
