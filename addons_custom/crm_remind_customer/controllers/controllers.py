# -*- coding: utf-8 -*-
from odoo import http

# class CrmRemindCustomer(http.Controller):
#     @http.route('/crm_remind_customer/crm_remind_customer/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/crm_remind_customer/crm_remind_customer/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('crm_remind_customer.listing', {
#             'root': '/crm_remind_customer/crm_remind_customer',
#             'objects': http.request.env['crm_remind_customer.crm_remind_customer'].search([]),
#         })

#     @http.route('/crm_remind_customer/crm_remind_customer/objects/<model("crm_remind_customer.crm_remind_customer"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('crm_remind_customer.object', {
#             'object': obj
#         })