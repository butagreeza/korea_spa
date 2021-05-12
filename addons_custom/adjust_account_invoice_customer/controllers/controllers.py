# -*- coding: utf-8 -*-
from odoo import http

# class AdjustAccountInvoiceCustomer(http.Controller):
#     @http.route('/adjust_account_invoice_customer/adjust_account_invoice_customer/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/adjust_account_invoice_customer/adjust_account_invoice_customer/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('adjust_account_invoice_customer.listing', {
#             'root': '/adjust_account_invoice_customer/adjust_account_invoice_customer',
#             'objects': http.request.env['adjust_account_invoice_customer.adjust_account_invoice_customer'].search([]),
#         })

#     @http.route('/adjust_account_invoice_customer/adjust_account_invoice_customer/objects/<model("adjust_account_invoice_customer.adjust_account_invoice_customer"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('adjust_account_invoice_customer.object', {
#             'object': obj
#         })