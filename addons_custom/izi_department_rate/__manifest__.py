# -*- coding: utf-8 -*-
{
    'name': "Department Rate",

    'summary': """
        Department Rate
    """,

    'description': """
        Department Rate
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list

    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'izi_use_service_card', 'pos_destroy_service'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_department_view.xml',
        'views/popup_customer_rate_view.xml',
        'views/res_partner_view.xml',
        'views/use_service_card_view.xml',
        'views/department_rate_line.xml',

    ],
}
