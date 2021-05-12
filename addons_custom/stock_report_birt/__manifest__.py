# -*- coding: utf-8 -*-
{
    'name': "Stock Report Birt",

    'summary': """
       Stock Report""",

    'description': """
        Stock Report
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'izi_use_service_card'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/rpt_ton_kho_so_luong_view.xml',
        'views/rpt_stock_inventory_delivery_view.xml',
        'views/report_stock_picking_detail_view.xml',
        'views/report_general_product_partner_use_view.xml',
        'views/report_in_out_detail_product_to_partner_view.xml',
        'views/report_in_out_cost_view.xml',
        'views/report_out_service_bom_view.xml',
        'views/report_service_bom_view.xml',
        'views/report_inventory_stock_view.xml',
        'views/report_stock_product_refund_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}