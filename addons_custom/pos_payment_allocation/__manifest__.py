# -*- coding: utf-8 -*-
{
    'name': "Pos Payment Allocation",

    'summary': """
        Pos Payment Allocation""",

    'description': """
        Pos Payment Allocation
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Point Of Sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'izi_product_release', 'izi_pos_custom_backend', 'pos_destroy_service'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/pos_payment_allocation_view.xml',
        'views/product_relase_view.xml',
        'views/pos_order_view.xml',
        'views/pos_destroy_service_view.xml',
        'views/invoice_make_payment_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}