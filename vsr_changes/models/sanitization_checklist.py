from odoo import models, fields, api

class SanitizationChecklist(models.Model):
    _name = 'sanitization.checklist'
    _description = 'Sanitization & Cleanliness Checklist'
    _rec_name = 'date'

    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    shift = fields.Selection([
        ('morning', 'Morning'),
        ('evening', 'Evening'),
        ('night', 'Night')
    ], string='Shift')
    area = fields.Char(string='Area')
    
    checklist_type = fields.Selection([
        ('packing', 'Packing'),
        ('production', 'Production'),
        ('barrel', 'Barrel')
    ], string='Type', required=True, default='production')

    checked_by = fields.Many2one('res.users', string='Checked By', default=lambda self: self.env.user)
    approved_by = fields.Many2one('res.users', string='Approved By')
    
    line_ids = fields.One2many('sanitization.checklist.line', 'checklist_id', string='Checklist Lines')
    
    overall_status = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('not_satisfactory', 'Not Satisfactory')
    ], string='Overall Status')
    
    supervisor_signature = fields.Char(string='Supervisor Signature (Name)')
    supervisor_date = fields.Date(string='Supervisor Sign Date')
    
    @api.model
    def default_get(self, fields_list):
        res = super(SanitizationChecklist, self).default_get(fields_list)
        if 'line_ids' in fields_list:
            lines = [
                (0, 0, {'sequence': 1, 'area_equipment': 'Drainage Lines & Traps', 'sanitization_requirement': 'No blockage, no foul odor, properly cleaned'}),
                (0, 0, {'sequence': 2, 'area_equipment': 'Processing Floor', 'sanitization_requirement': 'Clean, dry, no oil/water spillage'}),
                (0, 0, {'sequence': 3, 'area_equipment': 'Walls & Corners', 'sanitization_requirement': 'No mold, stains, or peeling paint'}),
                (0, 0, {'sequence': 4, 'area_equipment': 'Ceiling & Exhaust Fans', 'sanitization_requirement': 'Dust-free, no condensation'}),
                (0, 0, {'sequence': 5, 'area_equipment': 'Cutting Tables', 'sanitization_requirement': 'Cleaned & sanitized before/after use'}),
                (0, 0, {'sequence': 6, 'area_equipment': 'Mixing Tanks / Vessels', 'sanitization_requirement': 'No residue, CIP completed'}),
                (0, 0, {'sequence': 7, 'area_equipment': 'Barrels / Drums', 'sanitization_requirement': 'Washed, sanitized, covered'}),
                (0, 0, {'sequence': 8, 'area_equipment': 'Conveyors / Tools', 'sanitization_requirement': 'Food-contact safe & sanitized'}),
                (0, 0, {'sequence': 9, 'area_equipment': 'Weighing Scales', 'sanitization_requirement': 'Clean, accurate, no spillage'}),
                (0, 0, {'sequence': 10, 'area_equipment': 'Waste Bins', 'sanitization_requirement': 'Covered, cleaned, emptied regularly'}),
                (0, 0, {'sequence': 11, 'area_equipment': 'Hand Wash Stations', 'sanitization_requirement': 'Soap, sanitizer, water available'}),
                (0, 0, {'sequence': 12, 'area_equipment': 'Employee Hygiene', 'sanitization_requirement': 'Proper uniform, gloves, hair cover'}),
                (0, 0, {'sequence': 13, 'area_equipment': 'Chemical Storage Area', 'sanitization_requirement': 'Labeled, segregated, locked'}),
                (0, 0, {'sequence': 14, 'area_equipment': 'Pest Control Devices', 'sanitization_requirement': 'In place, clean, effective'}),
            ]
            res['line_ids'] = lines
        return res

class SanitizationChecklistLine(models.Model):
    _name = 'sanitization.checklist.line'
    _description = 'Sanitization Checklist Line'

    checklist_id = fields.Many2one('sanitization.checklist', string='Checklist')
    sequence = fields.Integer(string='S.No')
    area_equipment = fields.Char(string='Area/Equipment')
    sanitization_requirement = fields.Char(string='Sanitization Requirement')
    status = fields.Selection([
        ('ok', 'OK'),
        ('not_ok', 'Not OK')
    ], string='Status')
    corrective_action = fields.Char(string='Corrective Action')
    remarks = fields.Char(string='Remarks')
