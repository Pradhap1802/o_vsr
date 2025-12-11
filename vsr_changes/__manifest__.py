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
    'depends': ['stock', 'sale', 'account'],
    'data': [
        'views/stock_picking_views.xml',
        'views/stock_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
