# -*- coding: utf-8 -*-
from odoo import http

# class PosPaymentWithCoin(http.Controller):
#     @http.route('/pos_payment_with_coin/pos_payment_with_coin/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_payment_with_coin/pos_payment_with_coin/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_payment_with_coin.listing', {
#             'root': '/pos_payment_with_coin/pos_payment_with_coin',
#             'objects': http.request.env['pos_payment_with_coin.pos_payment_with_coin'].search([]),
#         })

#     @http.route('/pos_payment_with_coin/pos_payment_with_coin/objects/<model("pos_payment_with_coin.pos_payment_with_coin"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_payment_with_coin.object', {
#             'object': obj
#         })