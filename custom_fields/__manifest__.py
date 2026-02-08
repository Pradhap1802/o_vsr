{
    'name': 'Tally Integration Fields',
    'version': '18.0.1.0.0',
    'category': 'Customizations',
    'summary': 'Add Tally reference fields to Sale Order, Purchase Order, Delivery, Invoice, and Payment forms',
    'description': """
        This module adds Tally-related custom fields to various form views:
        - Sale Order: x_studio_tally_order_no
        - Purchase Order: x_studio_tally_order_no
        - Delivery: x_studio_delivery_ref_no, x_studio_receipt_ref_no
        - Invoice: x_studio_tally_sales_no, x_studio_tally_purchase_no
        - Payment: x_studio_tally_receipt_no
        
        All fields are organized under a 'Tally' notebook tab.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'sale_management',
        'purchase',
        'stock',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
