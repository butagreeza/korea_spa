# -*- coding: utf-8 -*-
{
    'name': "HR Custom",

    'summary': """
        HR Custom""",

    'description': """
        HR Custom
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'hr',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr','izi_branch'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/hr_department_custom_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_job_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}