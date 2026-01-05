from odoo import models, fields, api


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    bom_category = fields.Selection([
        ('salted_brine', 'Salted/Brine'),
        ('semi_finished', 'Semi Finished'),
        ('finished', 'Finished'),
    ], string='BOM Category', help='Category for grouping Bills of Materials')
