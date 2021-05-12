# -*- coding: utf-8 -*-
from odoo import http

# class IziMergeUseService(http.Controller):
#     @http.route('/izi_merge_use_service/izi_merge_use_service/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_merge_use_service/izi_merge_use_service/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_merge_use_service.listing', {
#             'root': '/izi_merge_use_service/izi_merge_use_service',
#             'objects': http.request.env['izi_merge_use_service.izi_merge_use_service'].search([]),
#         })

#     @http.route('/izi_merge_use_service/izi_merge_use_service/objects/<model("izi_merge_use_service.izi_merge_use_service"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_merge_use_service.object', {
#             'object': obj
#         })