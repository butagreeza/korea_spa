# -*- coding: utf-8 -*-
{
    'name': "Remind Customer",

    'summary': """
        Remind Customer""",

    'description': """
        Remind Customer
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'crm',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'izi_use_service_card', 'izi_vip', 'calendar','survey'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security_view.xml',
        'data/ir_sequence_data.xml',
        'views/product_customer_view.xml',
        'views/service_calender_reminder_view.xml',
        'views/calender_event_view.xml',
        'views/job_crm_reminder_view.xml',
        'views/res_partner_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}