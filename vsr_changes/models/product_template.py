from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pieces_per_case = fields.Integer(
        string='Pieces', 
        default=1, 
        help="Number of pieces in this product unit"
    )
    
    price_per_piece = fields.Float(
        string='Price/Piece',
        digits='Product Price',
        help="Manual price per piece"
    )
