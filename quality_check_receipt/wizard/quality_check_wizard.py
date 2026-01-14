from odoo import models, fields, api


class QualityCheckWizard(models.TransientModel):
    _name = 'quality.check.wizard'
    _description = 'Quality Check Wizard'

    picking_id = fields.Many2one('stock.picking', string='Receipt', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True, 
                                  domain="[('id', 'in', available_product_ids)]")
    available_product_ids = fields.Many2many('product.product', compute='_compute_available_products')
    team_id = fields.Many2one('quality.alert.team', string='Team', required=True, readonly=True)
    test_type_id = fields.Many2one('quality.point.test_type', string='Test Type', required=True, readonly=True)
    note = fields.Text(string='Note')
    product_type = fields.Selection([
        ('wad', 'WAD'),
        ('jar', 'JAR'),
        ('label', 'LABEL'),
        ('pouch_roll', 'POUCH/ROLL'),
        ('carton', 'CARTON/COTTON BOX'),
        ('other', 'Other')
    ], string='Product Type', compute='_compute_product_type', store=False)

    # WAD Fields
    wad_type = fields.Char(string='Wad Type')
    thickness_spec = fields.Char(string='Thickness (Spec)')
    size_dia_spec = fields.Char(string='Size / Dia (Spec - mm)')
    weight_piece_spec = fields.Char(string='Weight / Piece (Spec - g)')
    nos_kg_spec = fields.Char(string='Nos / Kg (Spec)')
    gumming = fields.Char(string='Gumming')
    damage_free = fields.Char(string='Damage Free')
    wad_ok = fields.Boolean(string='OK')
    wad_remarks = fields.Text(string='Remarks')

    # JAR Fields
    jar_capacity = fields.Char(string='Jar Capacity')
    height_spec = fields.Char(string='Height (Spec - mm)')
    diameter_spec = fields.Char(string='Diameter (Spec - mm)')
    neck_size_spec = fields.Char(string='Neck Size (Spec - mm)')
    weight_piece_jar_spec = fields.Char(string='Weight / Piece (Spec - g)')
    no_cracks = fields.Char(string='No Cracks')
    no_white_shading = fields.Char(string='No White Shading')
    neck_straight = fields.Char(string='Neck Straight')
    jar_ok = fields.Boolean(string='OK')
    jar_remarks = fields.Text(string='Remarks')

    # LABEL Fields
    label_type = fields.Char(string='Label Type')
    width_spec = fields.Char(string='Width (Spec - mm)')
    height_label_spec = fields.Char(string='Height (Spec - mm)')
    printing = fields.Char(string='Printing')
    colour = fields.Char(string='Colour')
    cutting = fields.Char(string='Cutting')
    gumming_label = fields.Char(string='Gumming')
    ingredients = fields.Char(string='Ingredients')
    barcode_no = fields.Char(string='Barcode No.')
    label_ok = fields.Boolean(string='OK')
    label_remarks = fields.Text(string='Remarks')

    # POUCH/ROLL Fields
    pouch_type = fields.Char(string='Type')
    width_pouch_spec = fields.Char(string='Width (Spec - mm)')
    height_pouch_spec = fields.Char(string='Height (Spec - mm)')
    bottom_gusset_spec = fields.Char(string='Bottom Gusset (Spec - mm)')
    nos_kg_pouch_spec = fields.Char(string='Nos / Kg (Spec)')
    weight_piece_pouch_spec = fields.Char(string='Weight / Piece (Spec - g)')
    no_delamination = fields.Char(string='No Delamination')
    pouch_ok = fields.Boolean(string='OK')
    pouch_remarks = fields.Text(string='Remarks')

    # CARTON/COTTON BOX Fields
    box_type = fields.Char(string='Box Type')
    length_spec = fields.Char(string='Length (Spec - mm)')
    width_carton_spec = fields.Char(string='Width (Spec - mm)')
    height_carton_spec = fields.Char(string='Height (Spec - mm)')
    ply_spec = fields.Char(string='Ply (Spec)')
    capacity_spec = fields.Char(string='Capacity (Spec - Nos)')
    printing_carton = fields.Char(string='Printing')
    carton_ok = fields.Boolean(string='OK')
    carton_remarks = fields.Text(string='Remarks')

    @api.depends('picking_id')
    def _compute_available_products(self):
        """Get products from the receipt moves"""
        for wizard in self:
            if wizard.picking_id:
                product_ids = wizard.picking_id.move_ids_without_package.mapped('product_id').ids
                wizard.available_product_ids = [(6, 0, product_ids)]
            else:
                wizard.available_product_ids = [(6, 0, [])]

    @api.depends('product_id')
    def _compute_product_type(self):
        """Determine product type based on product name suffix"""
        for wizard in self:
            if wizard.product_id and wizard.product_id.name:
                product_name = wizard.product_id.name.lower()
                if product_name.endswith('wad'):
                    wizard.product_type = 'wad'
                elif product_name.endswith('jar'):
                    wizard.product_type = 'jar'
                elif product_name.endswith('label'):
                    wizard.product_type = 'label'
                elif product_name.endswith('pouch') or product_name.endswith('roll'):
                    wizard.product_type = 'pouch_roll'
                elif product_name.endswith('carton') or 'cotton box' in product_name:
                    wizard.product_type = 'carton'
                else:
                    wizard.product_type = 'other'
            else:
                wizard.product_type = 'other'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Clear fields when product changes"""
        # This will trigger the recomputation of product_type
        # and the view will hide/show appropriate fields
        pass

    def _prepare_quality_check_vals(self):
        """Prepare values for quality check creation"""
        vals = {
            'picking_id': self.picking_id.id,
            'product_id': self.product_id.id,
            'team_id': self.team_id.id,
            'test_type_id': self.test_type_id.id,
            'note': self.note,
        }

        # Add product-specific fields based on product type
        if self.product_type == 'wad':
            vals.update({
                'wad_type': self.wad_type,
                'thickness_spec': self.thickness_spec,
                'size_dia_spec': self.size_dia_spec,
                'weight_piece_spec': self.weight_piece_spec,
                'nos_kg_spec': self.nos_kg_spec,
                'gumming': self.gumming,
                'damage_free': self.damage_free,
                'wad_ok': self.wad_ok,
                'wad_remarks': self.wad_remarks,
            })
        elif self.product_type == 'jar':
            vals.update({
                'jar_capacity': self.jar_capacity,
                'height_spec': self.height_spec,
                'diameter_spec': self.diameter_spec,
                'neck_size_spec': self.neck_size_spec,
                'weight_piece_jar_spec': self.weight_piece_jar_spec,
                'no_cracks': self.no_cracks,
                'no_white_shading': self.no_white_shading,
                'neck_straight': self.neck_straight,
                'jar_ok': self.jar_ok,
                'jar_remarks': self.jar_remarks,
            })
        elif self.product_type == 'label':
            vals.update({
                'label_type': self.label_type,
                'width_spec': self.width_spec,
                'height_label_spec': self.height_label_spec,
                'printing': self.printing,
                'colour': self.colour,
                'cutting': self.cutting,
                'gumming_label': self.gumming_label,
                'ingredients': self.ingredients,
                'barcode_no': self.barcode_no,
                'label_ok': self.label_ok,
                'label_remarks': self.label_remarks,
            })
        elif self.product_type == 'pouch_roll':
            vals.update({
                'pouch_type': self.pouch_type,
                'width_pouch_spec': self.width_pouch_spec,
                'height_pouch_spec': self.height_pouch_spec,
                'bottom_gusset_spec': self.bottom_gusset_spec,
                'nos_kg_pouch_spec': self.nos_kg_pouch_spec,
                'weight_piece_pouch_spec': self.weight_piece_pouch_spec,
                'no_delamination': self.no_delamination,
                'pouch_ok': self.pouch_ok,
                'pouch_remarks': self.pouch_remarks,
            })
        elif self.product_type == 'carton':
            vals.update({
                'box_type': self.box_type,
                'length_spec': self.length_spec,
                'width_carton_spec': self.width_carton_spec,
                'height_carton_spec': self.height_carton_spec,
                'ply_spec': self.ply_spec,
                'capacity_spec': self.capacity_spec,
                'printing_carton': self.printing_carton,
                'carton_ok': self.carton_ok,
                'carton_remarks': self.carton_remarks,
            })

        return vals

    def action_pass(self):
        """Update quality check with Pass result"""
        self.ensure_one()
        quality_check_id = self.env.context.get('quality_check_id')
        if quality_check_id:
            quality_check = self.env['quality.check'].browse(quality_check_id)
            vals = self._prepare_quality_check_vals()
            vals['quality_state'] = 'pass'
            quality_check.write(vals)
        return {'type': 'ir.actions.act_window_close'}

    def action_fail(self):
        """Update quality check with Fail result"""
        self.ensure_one()
        quality_check_id = self.env.context.get('quality_check_id')
        if quality_check_id:
            quality_check = self.env['quality.check'].browse(quality_check_id)
            vals = self._prepare_quality_check_vals()
            vals['quality_state'] = 'fail'
            quality_check.write(vals)
        return {'type': 'ir.actions.act_window_close'}
