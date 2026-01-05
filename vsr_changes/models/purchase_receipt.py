from odoo import models, fields, api


class StockPickingVSR(models.Model):
    _inherit = 'stock.picking'

    area = fields.Char(string='Area', help='Area of the purchase receipt')
    supplier_id = fields.Many2one('res.partner', string='Supplier', help='Supplier information')
    wastage = fields.Float(string='Wastage', digits=(10, 2), help='Wastage percentage or amount')
    weight_slip = fields.Image(string='Weight Slip', max_width=1024, max_height=1024, help='Weight slip image')

    def get_tax_details(self):
        """Compute tax breakdown for the receipt"""
        tax_data = {}
        for move in self.move_ids:
            if move.vsr_tax_ids and move.subtotal:
                taxes = move.vsr_tax_ids.compute_all(
                    move.rate,
                    currency=move.currency_id,
                    quantity=move.product_uom_qty,
                    product=move.product_id,
                    partner=move.picking_id.partner_id
                )
                for tax_line in taxes['taxes']:
                    tax_name = tax_line['name']
                    amount = tax_line['amount']
                    if tax_name in tax_data:
                        tax_data[tax_name] += amount
                    else:
                        tax_data[tax_name] = amount
        return tax_data

    def button_wastage(self):
        """Open wastage wizard for the picking"""
        self.ensure_one()
        view = self.env.ref('stock.stock_scrap_form_view2')
        products = self.env['product.product']
        for move in self.move_ids:
            if move.state not in ('draft', 'cancel') and move.product_id.type in ('product', 'consu'):
                products |= move.product_id
        return {
            'name': 'Wastage',
            'view_mode': 'form',
            'res_model': 'stock.scrap',
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'context': {
                'default_picking_id': self.id,
                'product_ids': products.ids,
                'default_company_id': self.company_id.id
            },
            'target': 'new',
        }

    def _update_wastage_from_scrap(self):
        """Update wastage field and deduct from next transfer's demand based on scrap records"""
        for picking in self:
            # Search for all scrap records linked to this picking
            scrap_records = self.env['stock.scrap'].search([
                ('picking_id', '=', picking.id)
            ])
            
            if scrap_records:
                # Group wastage by product
                wastage_by_product = {}
                for scrap in scrap_records:
                    product_id = scrap.product_id.id
                    if product_id not in wastage_by_product:
                        wastage_by_product[product_id] = 0
                    wastage_by_product[product_id] += scrap.scrap_qty
                
                # Sum up all manually entered scrap quantities
                total_scrap_qty = sum(scrap.scrap_qty for scrap in scrap_records)
                
                # Update the wastage field in this picking
                picking.wastage = total_scrap_qty
                
                # Update next transfer's demand by deducting wastage
                destination_moves = picking.move_ids.mapped('move_dest_ids')
                
                if destination_moves:
                    # Get the pickings that contain these destination moves
                    next_pickings = destination_moves.mapped('picking_id')
                    
                    for next_picking in next_pickings:
                        # Deduct wastage from demand in the next transfer
                        for move in next_picking.move_ids:
                            if move.product_id.id in wastage_by_product:
                                wastage_qty = wastage_by_product[move.product_id.id]
                                
                                # Reduce demand (product_uom_qty) by wastage amount
                                if move.product_uom_qty >= wastage_qty:
                                    move.product_uom_qty -= wastage_qty
                                else:
                                    move.product_uom_qty = 0
                                
                                # Also update quantity to match demand
                                move.quantity = move.product_uom_qty


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
