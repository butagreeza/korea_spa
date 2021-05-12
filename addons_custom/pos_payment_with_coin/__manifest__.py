# -*- coding: utf-8 -*-
{
    'name': "Pos Payment With Coin",

    'summary': """
        Pos Payment With Coin""",

    'description': """
        Pos Payment With Coin
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/pos_payment_with_coin.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}