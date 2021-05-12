# -*- coding: utf-8 -*-
from odoo import http

# class IziNotificationApprove(http.Controller):
#     @http.route('/izi_notification_approve/izi_notification_approve/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_notification_approve/izi_notification_approve/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_notification_approve.listing', {
#             'root': '/izi_notification_approve/izi_notification_approve',
#             'objects': http.request.env['izi_notification_approve.izi_notification_approve'].search([]),
#         })

#     @http.route('/izi_notification_approve/izi_notification_approve/objects/<model("izi_notification_approve.izi_notification_approve"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_notification_approve.object', {
#             'object': obj
#         })