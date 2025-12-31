# -*- coding: utf-8 -*-
from odoo import fields, models


class MrpReport(models.Model):
    _inherit = 'mrp.report'

    total_wastage = fields.Float(
        "Total Wastage/Defectives", readonly=True,
        help="Total quantity scrapped/wasted in this manufacturing order"
    )

    def _select(self):
        select_str = super()._select()
        # Add wastage to the SELECT clause
        select_str += """,
                wastage.total_wastage AS total_wastage
        """
        return select_str

    def _from(self):
        from_str = super()._from()
        # Add JOIN for wastage
        from_str += """
            LEFT JOIN (
                SELECT
                    mo.id AS mo_id,
                    COALESCE(SUM(scrap.scrap_qty), 0.0) AS total_wastage
                FROM mrp_production AS mo
                LEFT JOIN stock_scrap AS scrap ON scrap.production_id = mo.id
                WHERE mo.state = 'done'
                    AND (scrap.state = 'done' OR scrap.state IS NULL)
                GROUP BY mo.id
            ) wastage ON wastage.mo_id = mo.id
        """
        return from_str

    def _group_by(self):
        group_by_str = super()._group_by()
        # Add wastage to the GROUP BY clause
        group_by_str += """,
                wastage.total_wastage
        """
        return group_by_str
