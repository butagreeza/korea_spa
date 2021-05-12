# -*- coding: utf-8 -*-
{
    'name': "izi_pos_therapy_bundle",

    'summary': """
        izi_pos_therapy_bundle""",

    'description': """
        izi_pos_therapy_bundle
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'izi_pos_custom_backend', 'izi_therapy_record', 'pos_payment_config'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/therapy_bundle_view.xml',
        'views/therapy_bundle_barem_view.xml',
        'views/pos_order_custom.xml',
        'views/therapy_record_view.xml',
        'views/pos_config_custom_view.xml',
        'views/invoice_make_payment_view_custom.xml',
        'views/product_category_views.xml',
    ],
    # only loaded in demonstration mode

}