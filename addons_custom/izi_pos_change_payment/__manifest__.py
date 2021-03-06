# -*- coding: utf-8 -*-
{
    'name': "Pos Change Payment",

    'summary': """
        Pos Change Payment""",

    'description': """
        Pos Change Payment
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'izi_pos_custom_backend', 'pos_revenue_allocation'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/pos_order_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}