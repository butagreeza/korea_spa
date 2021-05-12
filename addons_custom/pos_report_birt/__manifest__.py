# -*- coding: utf-8 -*-
{
    'name': "Pos Report",

    'summary': """
       Pos Report""",

    'description': """
        Pos report
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','point_of_sale','izi_branch',],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/rpt_employee_view.xml',
        # 'views/templates.xml',
        # 'views/report_by_payment_view.xml',
        'views/rpt_use_service_view.xml',
        'views/rpt_payment_session_view.xml',
        'views/rpt_pos_money_session_view.xml',
        'views/rpt_pos_revenue_allocation_view.xml',
        'views/rpt_service_with_employee_view.xml',
        # 'views/rpt_rank_partner_view.xml',
        # 'views/rpt_point_partner_view.xml',
        'views/rpt_cong_no_kh_view.xml',
        'views/rpt_cong_no_ncc_view.xml',
        'views/rpt_doanh_thu_master_view.xml',
        # 'views/rpt_dinh_luong_nvl_view.xml',
        'views/rpt_service_with_employee_default_use_view.xml',
        'views/rpt_revenue_detail_view.xml',
        'views/rpt_revenue_sum_view.xml',
        'views/report_revenue_by_month_view.xml',
        'views/report_statement_customer_by_date_view.xml',
        # 'views/rpt_product_order_view.xml',
        'views/report_incomming_spending_view.xml',
        'views/report_wage_service_employee_view.xml',
        'views/report_pos_guarantee_view.xml',
        'views/report_commission_to_partner_view.xml',
        'views/report_pos_refund_view.xml',
        'views/report_pos_actual_debt_view.xml',
        'views/report_pos_revenue_config_view.xml',
        'views/report_check_out_therapy_going_over_law_view.xml',
        'views/report_adjusted_remain_partner_view.xml',
        'views/report_revenue_product_by_month_view.xml',
        'views/report_account_cash_view.xml',
        'views/report_partner_win_lose_view.xml',
    ],
    # 'qweb': ['static/src/xml/*.xml'],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}