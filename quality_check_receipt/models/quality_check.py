from odoo import models, fields, api


class QualityCheck(models.Model):
    _inherit = 'quality.check'

    # Add product type field
    product_type = fields.Selection([
        ('wad', 'WAD'),
        ('jar', 'JAR'),
        ('label', 'LABEL'),
        ('pouch_roll', 'POUCH/ROLL'),
        ('carton', 'CARTON/COTTON BOX'),
        ('other', 'Other')
    ], string='Product Type', compute='_compute_product_type', store=True)

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

    @api.depends('product_id')
    def _compute_product_type(self):
        """Determine product type based on product name suffix"""
        for record in self:
            if record.product_id and record.product_id.name:
                product_name = record.product_id.name.lower()
                if product_name.endswith('wad'):
                    record.product_type = 'wad'
                elif product_name.endswith('jar'):
                    record.product_type = 'jar'
                elif product_name.endswith('label'):
                    record.product_type = 'label'
                elif product_name.endswith('pouch') or product_name.endswith('roll'):
                    record.product_type = 'pouch_roll'
                elif product_name.endswith('carton') or 'cotton box' in product_name:
                    record.product_type = 'carton'
                else:
                    record.product_type = 'other'
            else:
                record.product_type = 'other'

    def action_open_quality_check_wizard(self):
        """Override to open custom wizard with product-specific fields"""
        self.ensure_one()
        return {
            'name': 'Quality Check',
            'type': 'ir.actions.act_window',
            'res_model': 'quality.check.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.picking_id.id if self.picking_id else False,
                'default_product_id': self.product_id.id if self.product_id else False,
                'default_team_id': self.team_id.id if self.team_id else False,
                'default_test_type_id': self.test_type_id.id if self.test_type_id else False,
                'quality_check_id': self.id,
            }
        }

