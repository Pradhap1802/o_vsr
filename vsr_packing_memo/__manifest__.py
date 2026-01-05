{
    'name': 'VSR Packing Memo Report',
    'version': '18.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Packing Memo report for Manufacturing Orders',
    'description': '''
        This module adds a Packing Memo report to Manufacturing Orders.
        The report displays:
        - Product information
        - Raw Materials (BOM components)
        - Accepted quantity (produced)
        - Wastage/Defectives
        - Total Issue (consumed materials)
        - Total Final Product
        - Remarks
    ''',
    'author': 'Processdrive',
    'depends': ['mrp', 'vsr_changes'],
    'data': [
        'views/stock_scrap_views.xml',
        'views/packing_memo_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
