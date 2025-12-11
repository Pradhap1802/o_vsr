from odoo import models, fields, api


class StockPickingVSR(models.Model):
    _inherit = 'stock.picking'

    area = fields.Char(string='Area', help='Area of the purchase receipt')
    supplier_id = fields.Many2one('res.partner', string='Supplier', help='Supplier information')
    rate = fields.Float(string='Rate', digits=(10, 2), help='Rate per unit')
    wastage = fields.Float(string='Wastage', digits=(10, 2), help='Wastage percentage or amount')
    costing = fields.Float(string='Costing', digits=(10, 2), compute='_compute_costing', store=True, help='Total costing')
    weight_slip = fields.Image(string='Weight Slip', max_width=1024, max_height=1024, help='Weight slip image')

    @api.depends('rate', 'wastage')
    def _compute_costing(self):
        for record in self:
            record.costing = record.rate + (record.rate * (record.wastage or 0) / 100)

    def _update_wastage_from_scrap(self):
        """Update wastage field based on manually entered scrap records"""
        for picking in self:
            # Search for all scrap records linked to this picking
            scrap_records = self.env['stock.scrap'].search([
                ('picking_id', '=', picking.id)
            ])
            
            if scrap_records:
                # Sum up all manually entered scrap quantities
                total_scrap_qty = sum(scrap.scrap_qty for scrap in scrap_records)
                
                # Update the wastage field in this picking
                picking.wastage = total_scrap_qty
                
                # Also update wastage in all downstream transfers
                self._update_downstream_wastage(picking, total_scrap_qty)

    def _update_downstream_wastage(self, picking, wastage_qty):
        """Update wastage in all downstream (next) transfers and deduce demand/quantity"""
        # Find all moves from this picking that have destination moves
        destination_moves = picking.move_ids.mapped('move_dest_ids')
        
        if destination_moves:
            # Get the pickings that contain these destination moves
            next_pickings = destination_moves.mapped('picking_id')
            
            for next_picking in next_pickings:
                if next_picking.state == 'done':
                    # Update wastage in next picking
                    next_picking.wastage = wastage_qty
                    
                    # Deduct wastage from demand and quantity in the next transfer
                    for move in next_picking.move_ids:
                        # Reduce demand (product_uom_qty) by wastage amount
                        if move.product_uom_qty > wastage_qty:
                            move.product_uom_qty -= wastage_qty
                        else:
                            move.product_uom_qty = 0
                        
                        # Reduce quantity done (qty_done) by wastage amount if manually entered
                        if move.quantity_done > wastage_qty:
                            move.quantity_done -= wastage_qty
                        else:
                            move.quantity_done = 0
                    
                    # Continue to next level (recursive)
                    self._update_downstream_wastage(next_picking, wastage_qty)


class StockScrapVSR(models.Model):
    _inherit = 'stock.scrap'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to update wastage in picking when scrap is created"""
        scraps = super().create(vals_list)
        
        # Update wastage in associated pickings only when new scrap is created
        pickings_to_update = scraps.mapped('picking_id').filtered(lambda p: p)
        for picking in pickings_to_update:
            picking._update_wastage_from_scrap()
        
        return scraps

    def write(self, vals):
        """Override write to update wastage in picking when scrap is modified"""
        # Get pickings before update
        pickings_before = self.mapped('picking_id').filtered(lambda p: p)
        
        result = super().write(vals)
        
        # Update wastage in associated pickings if scrap_qty changed
        if 'scrap_qty' in vals or 'quantity' in vals or 'picking_id' in vals:
            pickings_after = self.mapped('picking_id').filtered(lambda p: p)
            all_pickings = (pickings_before | pickings_after)
            for picking in all_pickings:
                picking._update_wastage_from_scrap()
        
        return result

    def unlink(self):
        """Override unlink to update wastage when scrap is deleted"""
        picking_ids = self.mapped('picking_id').filtered(lambda p: p)
        result = super().unlink()
        
        # Update wastage in associated pickings after deletion
        for picking in picking_ids:
            picking._update_wastage_from_scrap()
        
        return result
