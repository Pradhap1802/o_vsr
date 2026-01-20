from odoo import models, fields, api
from odoo.exceptions import UserError

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    spare_part_ids = fields.One2many(
        'maintenance.spare.part.line', 
        'maintenance_id', 
        string='Spare Parts Used'
    )
    calibration = fields.Char(string='Calibration')

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    # Replaced detailed list with simple product list (tags)
    spare_part_product_ids = fields.Many2many(
        'product.product', 
        string='Allowed Spare Parts'
    )

class MaintenanceSparePartLine(models.Model):
    _name = 'maintenance.spare.part.line'
    _description = 'Spare Parts Used in Maintenance'

    maintenance_id = fields.Many2one('maintenance.request', string='Maintenance Request')
    # Related fields to help with domain filtering
    equipment_id = fields.Many2one('maintenance.equipment', related='maintenance_id.equipment_id', store=False)
    allowed_product_ids = fields.Many2many('product.product', related='equipment_id.spare_part_product_ids', store=False)

    product_id = fields.Many2one(
        'product.product', 
        string='Part/Product', 
        required=True,
        domain="[('id', 'in', allowed_product_ids)]" 
    )
    quantity = fields.Float(string='Quantity', default=1.0)
    uom_id = fields.Many2one('uom.uom', related='product_id.uom_id', string='Unit of Measure', readonly=True)
    date_used = fields.Date(string='Date', default=fields.Date.context_today)
    remarks = fields.Char(string='Remarks')
    move_id = fields.Many2one('stock.move', string='Stock Move', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            line._deduct_stock()
        return lines

    def _deduct_stock(self):
        for line in self:
            if line.product_id.type not in ['product', 'consu']:
                continue
            
            # Find a valid source location (Internal)
            location_id = self.env['stock.location'].search([('usage', '=', 'internal'), ('company_id', 'in', [False, self.env.company.id])], limit=1, order='id')
            if not location_id:
                raise UserError("No internal stock location found to deduct stock from.")

            if line.product_id.tracking != 'none':
                 # For now, we don't support lots in this simple view. 
                 raise UserError(f"Product {line.product_id.name} is tracked by Lot/Serial. Automatic deduction not supported without Lot selection.")

            # Validate availability
            quant = self.env['stock.quant'].search([
                ('product_id', '=', line.product_id.id),
                ('location_id', 'child_of', location_id.id)
            ])
            available_qty = sum(quant.mapped('quantity'))
            
            if line.product_id.type == 'product' and available_qty < line.quantity:
                raise UserError(f"Insufficient Stock for '{line.product_id.name}'.\n"
                                f"Required: {line.quantity} {line.uom_id.name}\n"
                                f"Available: {available_qty} {line.uom_id.name} in {location_id.display_name} (and children).")

            location_dest_id = self.env.ref('stock.stock_location_customers').id

            move = self.env['stock.move'].create({
                'name': f'Maintenance Consumer: {line.product_id.name}',
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.uom_id.id or line.product_id.uom_id.id,
                'location_id': location_id.id,
                'location_dest_id': location_dest_id,
                'origin': line.maintenance_id.name or 'New Maintenance',
                'state': 'draft',
            })
            
            move._action_confirm()
            move._action_assign() # Try to reserve
            
            # If available (or partial), consume it.
            # If confirmed (not available), we try to force it but if stricter settings apply, it might fail.
            move.picked = True
            move.quantity = line.quantity
            move._action_done()
            
            if move.state != 'done':
                 raise UserError(f"Stock deduction failed for {line.product_id.name}.\n"
                                 f"Attempted to move {line.quantity} {line.product_id.uom_id.name} from {location_id.display_name}.\n"
                                 f"Move State: {move.state}.\n"
                                 f"Check if you have enough stock in this specific location.")

            line.move_id = move.id

class MaintenanceEquipmentSparePart(models.Model):
    _name = 'maintenance.equipment.spare.part'
    _description = 'Spare Parts for Equipment'

    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment')
    product_id = fields.Many2one('product.product', string='Part/Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    uom_id = fields.Many2one('uom.uom', related='product_id.uom_id', string='Unit of Measure', readonly=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    remarks = fields.Char(string='Remarks')
