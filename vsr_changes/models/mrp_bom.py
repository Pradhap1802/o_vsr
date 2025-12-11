from odoo import models


class MrpBomVSR(models.Model):
    _inherit = 'mrp.bom'

    def get_bom_report_data(self):
        """Override to add operations_count to report data"""
        # Get the original data from parent
        data = super().get_bom_report_data()
        
        # Add operations count to determine if we should show "Packing Memo" or "Production Memo"
        if isinstance(data, dict):
            # Count operations in the BOM lines
            operations_count = len([line for line in data.get('lines', []) if line.get('type') == 'operation'])
            data['operations_count'] = operations_count
        
        return data
