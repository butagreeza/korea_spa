# -*- coding: utf-8 -*-
{
    'name': "Merge Use Service",

    'summary': """
        Merge Use Service""",

    'description': """
        Merge Use Service
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','izi_use_service_card'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/merge_user_service_view.xml',
        'views/pop_up_payment_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}