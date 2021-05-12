# -*- coding: utf-8 -*-
{
    'name': "Job Revenue Monthly",

    'summary': """
        Job Revenue Monthly
    """,

    'description': """
        Job Revenue Monthly
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'job',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','crm','res_partner_custom'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/job_revenue_monthly.xml',
        'views/revenue_monthly_program.xml'
    ],
}