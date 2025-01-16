# -*- coding: utf-8 -*-
{
    'name': "PPH21Module",

    'summary': """
        Calculate Tax PPH21
        """,

    'description': """
        Tax PPH21
    """,

    'author': "Doodex",
    'website': "https://www.doodex.net/",
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_payroll', 'hr_work_entry_contract_enterprise', ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/menupph21.xml',
        'views/pph21_ptkp_views.xml',
        'views/pph21_tarif_efektif_views.xml',
        'views/pph21_tax_views.xml',
        'views/hr_employee_inherit_views.xml',
        'views/compute_pph21.xml',
        'views/pph21_annual_views.xml',
        'data/kategori_data.xml',
        'data/status_data.xml',
        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
