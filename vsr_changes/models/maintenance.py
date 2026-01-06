from odoo import models, fields, api

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    spare_part_ids = fields.One2many(
        'maintenance.spare.part.line', 
        'maintenance_id', 
        string='Spare Parts Used'
    )

class MaintenanceSparePartLine(models.Model):
    _name = 'maintenance.spare.part.line'
    _description = 'Spare Parts Used in Maintenance'

    maintenance_id = fields.Many2one('maintenance.request', string='Maintenance Request')
    product_id = fields.Many2one('product.product', string='Part/Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    uom_id = fields.Many2one('uom.uom', related='product_id.uom_id', string='Unit of Measure', readonly=True)
    remarks = fields.Char(string='Remarks')
