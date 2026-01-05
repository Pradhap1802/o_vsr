# -*- coding: utf-8 -*-
{
    'name': 'Dispatch Report',
    'version': '1.0',
    'category': 'Uncategorized',
    'summary': 'Module Summary',
    'description': '''Module Description''',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'sale', 'stock'],
    'data': [
        'report/report_action.xml',
        'views/report_order_tracking.xml',
        'views/report_tracking_wizard.xml'
        
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}