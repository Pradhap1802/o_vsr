{
    'name': 'Target Tracking',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Track customer targets by district',
    'description': '''
        This module provides target tracking functionality:
        - Adds district field to res.partner
        - Automatically creates target tracking records for customers
        - Displays customers grouped by district
        - Tracks monthly targets and achievements
    ''',
    'author': 'Processdrive',
    'depends': ['base', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/target_tracking_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
