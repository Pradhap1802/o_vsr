{
    'name': 'VSR Changes',
    'version': '18.0.1.0.0',
    'category': 'Stock',
    'summary': 'Customizations for VSR stock operations',
    'description': '''
        This module provides customizations for VSR (Vendor-Supplied Returns) operations:
        - Adds VSR fields to stock.picking (Area, Supplier, Rate, Wastage, Weight Slip)
        - Changes the label of product_uom_qty field in stock.move from "Demand" to "Actual Received Quantity"
        - Applies changes to both tree and form views of stock.move
        - Handles wastage deduction from downstream transfers
    ''',
    'author': 'Processdrive',
    'depends': ['stock', 'sale', 'account','mrp', 'purchase_stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/purchase_order_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_move_views.xml',
        'views/stock_move_receipt_views.xml',
        'views/stock_scrap_views.xml',
        'views/bom_report_views.xml',
        'views/report_receipt_note.xml',
        'views/report_invoice.xml',
        'views/mrp_views.xml',
        'wizard/stock_statement_wizard.xml',
        'views/report_stock_statement.xml',
        'report/mrp_order.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'vsr_changes/static/src/xml/chatter_override.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
