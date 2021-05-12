# -*- coding: utf-8 -*-
{
    'name': "Crm Sale Program",

    'summary': """
       Lấy danh sách khách hàng sinh nhật trong tháng""",

    'description': """
    Lấy danh sách khách hàng sinh nhật trong tháng
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','account','izi_vip'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/crm_sale_program.xml',
        # 'views/crm_sale_program_partner.xml',
        'views/job_crm_sale_program.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}