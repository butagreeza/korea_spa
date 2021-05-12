# -*- coding: utf-8 -*-
{
    'name': "Report Pos Pivot",

    'summary': """
        Report Pos Pivot""",

    'description': """
        Report Pos Pivot
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tungpd',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'res_partner_custom', 'point_of_sale'],

    # always loaded
    'data': [
        'wizard/report_by_payment_views.xml',
        'wizard/report_sale_by_product_views.xml',
        'wizard/report_cash_book_views.xml',
        'wizard/report_expense_income_by_product.xml',
        'wizard/report_expense_by_partner.xml',
        'wizard/report_expense_income_by_product.xml',
        'wizard/report_income_by_journal.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}