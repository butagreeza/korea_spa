# -*- coding: utf-8 -*-
{
    'name': "izi_crm_interaction",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'izi_crm_booking', 'point_of_sale', 'izi_therapy_record'],

    # always loaded
    'data': [
        'data/data_activity_history_job.xml',
        'security/ir.model.access.csv',
        'views/acivity_history_assign_view.xml',
        'views/partner_interaction_views.xml',
        'views/product_category_views.xml',
        'views/activity_history_views.xml',
        'views/product_product_views.xml',
        'views/therapy_record_view.xml',
        'views/partner_interaction_meeting_views.xml',
        'views/schedule_transfer_reason_views.xml',
        'views/res_partner_views.xml',
        'views/interaction_criteria_view.xml',
        'views/activity_history_resource.xml',
        'views/acivity_history_create_multi_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'qweb': [
             'static/src/xml/float_minutes_seconds_view.xml',]
}