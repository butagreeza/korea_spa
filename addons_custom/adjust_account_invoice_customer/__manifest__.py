# -*- coding: utf-8 -*-
{
    'name': "Adjust Account Invoice Customer",

    'summary': """
        Adjust Account Invoice Customer""",

    'description': """
        Adjust Account Invoice Customer By SangLa
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','izi_pos_custom_backend', 'pos_security'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/adjust_account_invoice_customer_view.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}