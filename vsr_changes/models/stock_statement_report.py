from odoo import models, api, _

class StockStatementReport(models.AbstractModel):
    _name = 'report.vsr_changes.report_stock_statement'
    _description = 'Stock Statement Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            return {}
        
        date_start = data.get('date_start')
        date_end = data.get('date_end')
        company_id = data.get('company_id')
        category_ids = data.get('category_ids')
        
        # Build SQL query
        where_categ = ""
        if category_ids:
            where_categ = f"AND pt.categ_id IN ({','.join(map(str, category_ids))})"

        query = f"""
            SELECT 
                categ.name as category_name,
                p.default_code as code,
                pt.name->>'en_US' as name, 
                m.product_id,
                -- Opening: Moves before start date
                SUM(CASE 
                    WHEN m.date < %s AND ld.usage = 'internal' AND ls.usage != 'internal' THEN m.product_qty 
                    WHEN m.date < %s AND ls.usage = 'internal' AND ld.usage != 'internal' THEN -m.product_qty 
                    ELSE 0 END) as opening,
                -- Receipt: Incoming from Vendor/Transit (In period)
                SUM(CASE 
                    WHEN m.date >= %s AND m.date <= %s AND ld.usage = 'internal' AND ls.usage not in ('internal', 'inventory', 'production') THEN m.product_qty 
                    ELSE 0 END) as receipt,
                -- Issue: Out to Production (In period)
                SUM(CASE 
                    WHEN m.date >= %s AND m.date <= %s AND ls.usage = 'internal' AND ld.usage = 'production' THEN m.product_qty 
                    ELSE 0 END) as issue,
                -- Difference: Wastage/Scrap (In period)
                SUM(CASE 
                    WHEN m.date >= %s AND m.date <= %s AND ls.usage = 'internal' AND (m.scrapped = true OR ld.usage = 'inventory') AND NOT (ld.usage = 'inventory' AND m.scrapped = false) THEN m.product_qty
                    ELSE 0 END) as difference,
                -- Physical: Inventory Adjustments (In period)
                SUM(CASE 
                    WHEN m.date >= %s AND m.date <= %s AND ld.usage = 'internal' AND ls.usage = 'inventory' THEN m.product_qty 
                    WHEN m.date >= %s AND m.date <= %s AND ls.usage = 'internal' AND ld.usage = 'inventory' AND m.scrapped = false THEN -m.product_qty
                    ELSE 0 END) as physical
            FROM product_product p
            JOIN product_template pt ON p.product_tmpl_id = pt.id
            JOIN product_category categ ON pt.categ_id = categ.id
            LEFT JOIN stock_move m ON m.product_id = p.id AND m.state = 'done' AND m.company_id = %s
            LEFT JOIN stock_location ls ON m.location_id = ls.id
            LEFT JOIN stock_location ld ON m.location_dest_id = ld.id
            WHERE pt.type IN ('product', 'consu')
            {where_categ}
            GROUP BY categ.name, m.product_id, p.default_code, pt.name, p.id
            ORDER BY categ.name, pt.name
        """
        
        # Logging for debug
        # import logging
        # _logger = logging.getLogger(__name__)
        # _logger.info("Stock Statement Query: %s", query)
        # _logger.info("Stock Statement Params: %s", params)

        
        params = [date_start, date_start, 
                  date_start, date_end, 
                  date_start, date_end,
                  date_start, date_end,
                  date_start, date_end, date_start, date_end,
                  company_id]
        
        self.env.cr.execute(query, tuple(params))
        lines = self.env.cr.dictfetchall()
        
        # Prepare groupings
        grouped_lines = {}
        for line in lines:
            line['opening'] = line['opening'] or 0.0
            line['receipt'] = line['receipt'] or 0.0
            line['issue'] = line['issue'] or 0.0
            line['difference'] = line['difference'] or 0.0
            line['physical'] = line['physical'] or 0.0
            
            line['total'] = line['opening'] + line['receipt']
            # Closing = Total - Issue - Difference + Physical (Adjustment)
            # Or Closing = Stock at End (Opening + All In - All Out).
            # Let's calculate purely:
            # Net change = Receipt - Issue - Difference + Physical ? 
            # Check Physical logic: In from Inv (+), Out to Inv (-). So (+ Physical).
            # Check Receipt logic: In from Vendor (+).
            # Check Issue logic: Out to Prod (-).
            # Check Difference: Out to Scrap (-).
            # Missing: Out to Customer? (Assuming Report specific to Raw Materials).
            
            line['closing'] = line['opening'] + line['receipt'] - line['issue'] - line['difference'] + line['physical']
            
            categ = line['category_name']
            if categ not in grouped_lines:
                grouped_lines[categ] = []
            grouped_lines[categ].append(line)

        company = self.env['res.company'].browse(company_id)

        return {
            'doc_ids': docids,
            'doc_model': 'vsr.stock.statement.wizard',
            'data': data,
            'lines': grouped_lines,
            'date_start': date_start,
            'date_end': date_end,
            'company': company,
        }
