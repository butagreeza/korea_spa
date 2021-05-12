# -*- coding: utf-8 -*-
{
    'name': "CRM Report",

    'summary': """
       CRM Report""",

    'description': """
        CRM Report
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'point_of_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/rpt_crm_fail.xml',
        'views/rpt_crm_customer_new.xml',
        'views/crm_service_reminder_calender_view.xml',
        'views/rpt_partner_not_revenue_date_view.xml',
        'views/rpt_birthday_partner_view.xml',
        'views/rpt_crm_state_view.xml',
        'views/rpt_revenue_detail_default_use_view.xml',
        'views/rpt_revenue_sum_view.xml',
        'views/rpt_birthday_partner_korea_view.xml',
        'views/report_job_performance_view.xml',
        'views/report_partner_feedback_view.xml',
        'views/report_care_customer_to_counselor_view.xml',
        'views/report_give_gift_partner_view.xml',
        'views/report_interaction_partner_view.xml',
        'views/report_job_handling_by_department_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}