{
    'name': 'Quality Check Receipt',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Product-specific quality checks for receipts',
    'description': '''
        Quality Check Receipt Module
        =============================
        
        This module adds product-specific quality check functionality for receipts:
        - Quality check wizard with product-specific fields
        - Support for WAD, JAR, LABEL, POUCH/ROLL, and CARTON/COTTON BOX products
        - Pass/Fail quality check results
        - Quality check history linked to receipts
        - Smart button to view all quality checks
    ''',
    'author': 'Processdrive',
    'depends': ['stock', 'product', 'quality_control'],
    'data': [
        'security/ir.model.access.csv',
        'views/quality_check_views.xml',
        'views/stock_picking_views.xml',
        'wizard/quality_check_wizard_views.xml',
        'reports/quality_check_worksheet_reports.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
