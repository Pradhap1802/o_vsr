from odoo import models, fields, api

class RiskAssessment(models.Model):
    _name = 'risk.assessment'
    _description = 'Construction Risk Assessment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Risk Assess. No.', required=True, copy=False, readonly=True, index=True, default='New')
    project_title = fields.Char(string='Project Title')
    task_activity = fields.Text(string='Task/Activity')
    project_no = fields.Char(string='Project No.')
    date_prepared = fields.Date(string='Date Prepared', default=fields.Date.context_today)

    hazard_ids = fields.One2many('risk.assessment.line', 'assessment_id', string='Hazards')

    # Persons Affected
    person_operative = fields.Boolean('Operatives')
    person_other_worker = fields.Boolean('Other Workers')
    person_other = fields.Boolean('Others')
    person_public = fields.Boolean('Members of Public')
    person_manager = fields.Boolean('Managers')
    person_visitor = fields.Boolean('Site Visitors')
    person_young = fields.Boolean('Young Persons')

    # PPE Requirements
    ppe_harness = fields.Boolean('Harness & Lanyard')
    ppe_hearing = fields.Boolean('Hearing Protection')
    ppe_gloves = fields.Boolean('Gloves')
    ppe_hiviz = fields.Boolean('Hi-Viz Clothing')
    ppe_eye = fields.Boolean('Eye Protection')
    ppe_boots = fields.Boolean('Boots')
    ppe_respiratory = fields.Boolean('Respiratory Protection')
    ppe_head = fields.Boolean('Head Protection')
    ppe_overalls = fields.Boolean('Approved Overalls')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('risk.assessment') or 'New'
        return super().create(vals_list)

class RiskAssessmentLine(models.Model):
    _name = 'risk.assessment.line'
    _description = 'Risk Assessment Hazard Line'

    assessment_id = fields.Many2one('risk.assessment', string='Assessment', required=True, ondelete='cascade')
    project_title = fields.Char(related='assessment_id.project_title', string='Project Title', store=True, readonly=True)
    date_prepared = fields.Date(related='assessment_id.date_prepared', string='Date Prepared', store=True, readonly=True)
    ref = fields.Char(string='Ref.')
    hazard_description = fields.Text(string='Key Hazards')
    
    likelihood = fields.Selection([
        ('3', 'Probable (3)'),
        ('2', 'Occasional (2)'),
        ('1', 'Remote (1)')
    ], string='Likelihood', default='1', required=True)

    severity = fields.Selection([
        ('5', 'Catastrophic (5)'),
        ('4', 'Critical (4)'),
        ('3', 'Serious (3)'),
        ('2', 'Marginal (2)'),
        ('1', 'Negligible (1)')
    ], string='Severity', default='1', required=True)

    risk_score = fields.Integer(string='Risk Score', compute='_compute_risk_score', store=True)

    @api.depends('likelihood', 'severity')
    def _compute_risk_score(self):
        for line in self:
            l = int(line.likelihood or 0)
            s = int(line.severity or 0)
            line.risk_score = l * s
