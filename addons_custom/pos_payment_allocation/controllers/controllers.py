# -*- coding: utf-8 -*-
from odoo import http

# class PosPaymentAllocation(http.Controller):
#     @http.route('/pos_payment_allocation/pos_payment_allocation/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_payment_allocation/pos_payment_allocation/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_payment_allocation.listing', {
#             'root': '/pos_payment_allocation/pos_payment_allocation',
#             'objects': http.request.env['pos_payment_allocation.pos_payment_allocation'].search([]),
#         })

#     @http.route('/pos_payment_allocation/pos_payment_allocation/objects/<model("pos_payment_allocation.pos_payment_allocation"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_payment_allocation.object', {
#             'object': obj
#         })