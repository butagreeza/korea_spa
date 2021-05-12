# -*- coding: utf-8 -*-
from odoo import http

# class JobCustom(http.Controller):
#     @http.route('/job_custom/job_custom/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/job_custom/job_custom/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('job_custom.listing', {
#             'root': '/job_custom/job_custom',
#             'objects': http.request.env['job_custom.job_custom'].search([]),
#         })

#     @http.route('/job_custom/job_custom/objects/<model("job_custom.job_custom"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('job_custom.object', {
#             'object': obj
#         })