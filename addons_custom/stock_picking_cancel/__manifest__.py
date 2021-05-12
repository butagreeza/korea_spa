# -*- coding: utf-8 -*-
{
    'name': "Stock picking cancel",

    'summary': """
        Stock picking cancel module is used for cancel the picking or move and set it to draft stage.
        """,

    'description': """
        Stock picking cancel module is used for cancel the picking or move and set it to draft stage.
    """,
    'author': "Dev Happy",
    'category': 'Warehouse',
    'version': '12.0.1',
    'support':"dev.odoo.vn@gmail.com",
    'depends': ['stock'],
    'currency': 'EUR',
    'price': 49.99,
    'license': 'OPL-1',
    'data': [
        'security/stock_security.xml',
        'views/stock_picking_view.xml',
    ],
}