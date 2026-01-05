from odoo import models, api, _
from datetime import datetime, timedelta

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
        
        # Calculate previous day for opening stock
        # Handle both date and datetime formats by extracting only the date portion
        date_start_only = date_start.split(' ')[0] if ' ' in date_start else date_start
        date_start_obj = datetime.strptime(date_start_only, '%Y-%m-%d')
        previous_day = (date_start_obj - timedelta(days=1)).strftime('%Y-%m-%d')
        
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
                -- Opening: Closing stock from previous day (all moves before start date)
                SUM(CASE 
                    WHEN m.date < %s AND ld.usage = 'internal' AND ls.usage != 'internal' THEN m.product_qty 
                    WHEN m.date < %s AND ls.usage = 'internal' AND ld.usage != 'internal' THEN -m.product_qty 
                    ELSE 0 END) as opening,
                -- Receipt: All incoming to internal locations (In period)
                SUM(CASE 
                    WHEN m.date >= %s AND m.date <= %s AND ld.usage = 'internal' AND ls.usage != 'internal' THEN m.product_qty 
                    ELSE 0 END) as receipt,
                -- Issue: All outgoing from internal locations (In period)
                SUM(CASE 
                    WHEN m.date >= %s AND m.date <= %s AND ls.usage = 'internal' AND ld.usage != 'internal' THEN m.product_qty 
                    ELSE 0 END) as issue,
                -- Physical: Inventory adjustments (In period) - actual count
                SUM(CASE 
                    WHEN m.date >= %s AND m.date <= %s AND ld.usage = 'internal' AND ls.usage = 'inventory' THEN m.product_qty 
                    WHEN m.date >= %s AND m.date <= %s AND ls.usage = 'internal' AND ld.usage = 'inventory' THEN -m.product_qty
                    ELSE 0 END) as physical_adjustment
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
        
        params = [date_start, date_start,  # Opening
                  date_start, date_end,     # Receipt
                  date_start, date_end,     # Issue
                  date_start, date_end, date_start, date_end,  # Physical adjustment
                  company_id]
        
        self.env.cr.execute(query, tuple(params))
        lines = self.env.cr.dictfetchall()
        
        # Prepare groupings
        grouped_lines = {}
        for line in lines:
            line['opening'] = line['opening'] or 0.0
            line['receipt'] = line['receipt'] or 0.0
            line['issue'] = line['issue'] or 0.0
            physical_adjustment = line['physical_adjustment'] or 0.0
            
            # Total = Opening + Receipt
            line['total'] = line['opening'] + line['receipt']
            
            # Closing Stock = Opening + Receipt - Issue (calculated stock)
            line['closing'] = line['total'] - line['issue']
            
            # Physical Stock = Closing + Physical Adjustment
            # - If NO inventory adjustment done: physical_adjustment = 0, so Physical = Closing
            # - If inventory adjustment done: Physical = Closing + Adjustment (the actual counted stock)
            line['physical'] = physical_adjustment
            
            # Difference = Physical - Closing
            # - If Physical = Closing, then Difference = 0
            # - If Physical > Closing, then Difference is positive (surplus/gain)
            # - If Physical < Closing, then Difference is negative (shortage/loss)
            line['difference'] = line['physical'] - line['closing']
            
            # Only show difference if it's not zero
            if abs(line['difference']) < 0.01:  # Avoid floating point issues
                line['difference'] = 0.0
            
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
