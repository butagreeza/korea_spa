# -*- coding: utf-8 -*-
{
    'name': "izi_therapy_record",

    'summary': """
        izi_therapy_record""",

    'description': """
        izi_therapy_record
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'izi_vip', 'stock', 'izi_use_service_card',
                'izi_crm_lead', 'izi_pos_custom_backend', 'pos_payment_allocation', 'stock_picking_cancel',
                'izi_manage_room', 'pos_work_service_allocation', 'izi_department_rate'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/therapy_record_view.xml',
        'views/body_area_view.xml',
        'views/therapy_prescription_view.xml',
        'views/izi_service_card_using_custom_view.xml',
        'views/product_template_custom_view.xml',
        'views/therapy_return_product_view.xml',
        'views/crm_lead_views.xml',
        'views/product_product_view.xml',
        'views/res_partner_views.xml',
        'views/therapy_record_product_update_view.xml',
        'views/pos_work_service_allocation_line_views.xml',
        'qweb/qweb_work_service.xml',
        'views/popup_customer_rate_view.xml',
        # 'views/stock_picking_view.xml',
    ],
    "qweb": [
            'static/src/xml/measure_body_detail.xml',
    ],

    # only loaded in demonstration mode

}