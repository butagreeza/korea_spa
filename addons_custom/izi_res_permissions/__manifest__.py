# -*- coding: utf-8 -*-
{
    'name': "izi_res_permissions",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'izi_use_service_card',
                'pos_customer_deposit',
                'pos_commission_allocation',
                'izi_pos_custom_backend',
                'izi_pos_crm',
                'izi_crm_claim',
                'izi_crm_booking',
                'stock_inventory_customer',
                'izi_scan_barcode', 'crm_report_birt',
                'izi_crm_interaction',
                'izi_pos_change_payment',
                ],

    # always loaded
    'data': [
        'security/res_groups_branch.xml',
        'security/res_groups_general.xml',
        'security/ir.model.access.csv',
        'security/ir_rule_branch.xml',
        'views/crm_views.xml',
        'views/purchase_views.xml',
        'views/point_of_sale_views.xml',
        'views/stock_views.xml',
        'views/account_views.xml',
        'views/contacts_views.xml',
        'views/calendar_views.xml',
        'views/therapy_prescription_views.xml',
        'views/pos_order_views.xml',
        'views/res_partner_views.xml',
        'views/pos_customer_deposit_line_views.xml',
        'views/izi_service_card_using_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}