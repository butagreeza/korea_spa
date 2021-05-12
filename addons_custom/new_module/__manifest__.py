# -*- coding: utf-8 -*-
{
    'name': "New Module",

    'summary': """
       New Module
    """,

    'description': """
        New Module
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    'category': 'new_module',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'views/new_module_menu_view.xml',
    ],
}
