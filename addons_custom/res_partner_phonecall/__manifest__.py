# -*- coding: utf-8 -*-
{
    'name': "ResPartner PhoneCall",

    'summary': """
        ResPartner PhoneCall""",

    'description': """
        ResPartner PhoneCall
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': '',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'izi_crm_interaction', 'crm'],

    # always loaded
    'data': [
        'data/voip_phonecall_data.xml',
        'views/hotline_config_views.xml',
        'views/res_partner_views.xml',
        'views/phonecall_views.xml',
        'views/res_users_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}