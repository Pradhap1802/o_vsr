from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Note: This module extends quality.check with product-specific fields
    # The quality_control module already provides quality check functionality for stock.picking
    # No additional methods needed here
