# -*- coding: utf-8 -*-
from odoo import http

# class StockJobWarehouseOderpoint(http.Controller):
#     @http.route('/stock_job_warehouse_oderpoint/stock_job_warehouse_oderpoint/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stock_job_warehouse_oderpoint/stock_job_warehouse_oderpoint/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('stock_job_warehouse_oderpoint.listing', {
#             'root': '/stock_job_warehouse_oderpoint/stock_job_warehouse_oderpoint',
#             'objects': http.request.env['stock_job_warehouse_oderpoint.stock_job_warehouse_oderpoint'].search([]),
#         })

#     @http.route('/stock_job_warehouse_oderpoint/stock_job_warehouse_oderpoint/objects/<model("stock_job_warehouse_oderpoint.stock_job_warehouse_oderpoint"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stock_job_warehouse_oderpoint.object', {
#             'object': obj
#         })