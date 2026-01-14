# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PickleAnalysis(models.Model):
    _name = 'pickle.analysis'
    _description = 'Pickle Analysis Report for Salt & Acidity'
    _order = 'date desc, id desc'

    # Header Fields
    name = fields.Char(string='Report No', required=True, copy=False, readonly=True, default='New')
    factor_acidity = fields.Float(string='Factor: Acidity', digits=(16, 4), default=0.6)
    salt_factor = fields.Float(string='Salt Factor', digits=(16, 4), default=2.9225)
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    
    # Quality Attributes
    taste = fields.Char(string='Taste', help='Taste of the product')
    texture = fields.Char(string='Texture', help='Texture of the product (e.g., Crunchy, Soft)')
    color = fields.Char(string='Colour', help='Color of the product')
    smell = fields.Char(string='Smell/Odour', help='Smell or aroma of the product')
    overall_acceptability = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Overall Quality', default='pass')
    
    # Analysis Lines
    line_ids = fields.One2many('pickle.analysis.line', 'analysis_id', string='Analysis Lines')
    
    # Computed fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('pickle.analysis') or 'New'
        return super().create(vals_list)
    
    def action_confirm(self):
        self.write({'state': 'done'})
    
    def action_draft(self):
        self.write({'state': 'draft'})
    
    def action_cancel(self):
        self.write({'state': 'cancel'})


class PickleAnalysisLine(models.Model):
    _name = 'pickle.analysis.line'
    _description = 'Pickle Analysis Line'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    analysis_id = fields.Many2one('pickle.analysis', string='Analysis', required=True, ondelete='cascade')
    
    # Product Information
    product_id = fields.Many2one('product.product', string='Name of The Product', required=True)
    lot_no = fields.Char(string='Lot No')
    batch_size = fields.Float(string='Batch Size', digits=(16, 2))
    final_batch = fields.Float(string='Final', digits=(16, 2))
    
    # AgNO3 Titration Volume (Salt Analysis)
    agno3_initial = fields.Float(string='Initial (AgNO3)', digits=(16, 2))
    agno3_net_ml = fields.Float(string='Net ml (AgNO3)', digits=(16, 2), compute='_compute_agno3_net', store=True)
    agno3_percent_salt = fields.Float(string='% Salt', digits=(16, 2), compute='_compute_agno3_percent_salt', store=True)
    agno3_final = fields.Float(string='Final (AgNO3)', digits=(16, 2))
    
    # % of Acidity
    percent_acidity = fields.Float(string='% of Acidity', digits=(16, 2))
    
    # NaOH Titration Volume (Acidity Analysis)
    naoh_initial = fields.Float(string='Initial (NaOH)', digits=(16, 2))
    naoh_net_ml = fields.Float(string='Net ml (NaOH)', digits=(16, 2), compute='_compute_naoh_net', store=True)
    naoh_percent_acidity = fields.Float(string='% Acidity (NaOH)', digits=(16, 2), compute='_compute_naoh_percent_acidity', store=True)
    naoh_final = fields.Float(string='Final (NaOH)', digits=(16, 2))
    
    # Recommendations
    recommended_qty_salt = fields.Float(string='Recommended Qty of salt', digits=(16, 2))
    recommended_qty_aa = fields.Float(string='Recommended Qty of AA', digits=(16, 2))
    recommended_qty_ca = fields.Float(string='Recommended Qty of CA', digits=(16, 2))
    remarks = fields.Text(string='Remarks')
    
    @api.depends('agno3_final', 'agno3_initial')
    def _compute_agno3_net(self):
        for line in self:
            line.agno3_net_ml = line.agno3_final - line.agno3_initial
    
    @api.depends('agno3_net_ml', 'analysis_id.salt_factor')
    def _compute_agno3_percent_salt(self):
        for line in self:
            if line.agno3_net_ml and line.analysis_id.salt_factor:
                line.agno3_percent_salt = line.agno3_net_ml * line.analysis_id.salt_factor
            else:
                line.agno3_percent_salt = 0.0
    
    @api.depends('naoh_final', 'naoh_initial')
    def _compute_naoh_net(self):
        for line in self:
            line.naoh_net_ml = line.naoh_final - line.naoh_initial
    
    @api.depends('naoh_net_ml', 'analysis_id.factor_acidity')
    def _compute_naoh_percent_acidity(self):
        for line in self:
            if line.naoh_net_ml and line.analysis_id.factor_acidity:
                line.naoh_percent_acidity = line.naoh_net_ml * line.analysis_id.factor_acidity
            else:
                line.naoh_percent_acidity = 0.0
