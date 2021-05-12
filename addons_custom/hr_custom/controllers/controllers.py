# -*- coding: utf-8 -*-
from odoo import http

# class HrCustom(http.Controller):
#     @http.route('/hr_custom/hr_custom/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_custom/hr_custom/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_custom.listing', {
#             'root': '/hr_custom/hr_custom',
#             'objects': http.request.env['hr_custom.hr_custom'].search([]),
#         })

#     @http.route('/hr_custom/hr_custom/objects/<model("hr_custom.hr_custom"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_custom.object', {
#             'object': obj
#         })