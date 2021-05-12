# -*- coding: utf-8 -*-
{
    'name': "Accounting Change Subtotal",

    'summary': """
        Accounting change subtotal auto calculate price
        """,

    'description': """
        Accounting change subtotal auto calculate price
    """,

    'author': "ERPViet",
    'website': "https://www.erpviet.vn",
    'category': 'Invoicing Management',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account', 'purchase'],

    # always loaded
    'data': [
        'views/account_views.xml',
    ],

}