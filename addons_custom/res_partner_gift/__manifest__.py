# -*- coding: utf-8 -*-
{
    'name': "Partner Gift",

    'summary': """
        Partner Gift""",

    'description': """
        Partner Gift
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': '',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'izi_pos_custom_backend', 'izi_pos_change_payment', 'izi_product_release', 'izi_use_service_card', 'izi_res_permissions'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/pos_order_voucher_views.xml',
        'views/res_partner_view.xml',
        'views/product_product_views.xml',
        'views/payment_method_views.xml',
        'views/partner_gift_reason_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}