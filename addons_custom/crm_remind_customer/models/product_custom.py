# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductServiceCalender(models.Model):
    _name = 'product.service.reminder'

    name = fields.Char("Name")
    type = fields.Selection([('httn', "HTTN"), ('httb',"HTTB"), ('nlkh', "NLKH")]) # HTTN là hỏi thăm theo ngày, HTTB là hỏi thăm theo buổi, nlkh là nhắc lịch khách hàng
    value = fields.Float("Value")
    product_id = fields.Many2one('product.product', "Service")

class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_service_calender_reminder_ids = fields.One2many('product.service.reminder','product_id', "Service Calender Reminder")
