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
    'depends': ['mrp', 'vsr_changes', 'quality_control', 'mrp_account_enterprise'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_bom_views.xml',
        'views/mrp_production_views.xml',
        'views/stock_scrap_views.xml',
        'views/packing_memo_report.xml',
        'views/production_memo_report.xml',
        'views/pickle_analysis_views.xml',
        'views/risk_assessment_views.xml',
        'views/report_risk_assessment.xml',
        'views/vsr_coa_views.xml',
        'views/report_vsr_coa.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
