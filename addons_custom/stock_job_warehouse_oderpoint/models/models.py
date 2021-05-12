# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm
from datetime import datetime, date
from odoo.exceptions import except_orm, Warning as UserError
import logging
_logger = logging.getLogger(__name__)

class StockJobWarehouseOderpointSendMail(models.Model):
    _name = 'stock.warehouse.orderpoint.send.mail'

    name = fields.Char("Name")
    active = fields.Boolean("Active", default=True)
    date = fields.Date("Date", default=fields.Date.context_today)
    orderpoint_send_mail_ids = fields.One2many('stock.warehouse.orderpoint.send.mail.line', 'orderpoint_send_mail_id', "Send Mail")

    def job_send_mail_warepoint(self):
        location = self.env['stock.location'].search([('usage', '=', 'internal')])
        if not  location:
            raise except_orm("Thông báo!", ("Không có kho"))
        for line in location:
            body_mail = 'Sản phẩm hết hàng ngày ' + date.today().strftime("%d-%m-%Y") + ' trên kho ' + str(line.name) + '\n'
            warehouse_point = self.env['stock.warehouse.orderpoint'].search([('location_id', '=', line.id)])
            if warehouse_point:
                for x in warehouse_point:
                    if x.product_id.type != 'service':
                        total_availability = self.env['stock.quant']._get_available_quantity(x.product_id,
                                                                                             line)
                        if total_availability < x.product_min_qty:
                            body_mail += '\nSản phẩm ' + str(x.product_id.name) + ' số lượng còn là\t' + str(total_availability) + '\n'
                # sangla them send mail khi het hang 20/4/2019
                # mail_to = ''
                # mail_cc = ''
                # for y in self.orderpoint_send_mail_ids:
                #     if line.id == y.location_id.id:
                #
                partner_ids = []
                partner_ids.append(3)
                warehouse_point_send_obj = self.env['stock.warehouse.orderpoint.send.mail'].search([('active', '=', True)])
                if len(warehouse_point_send_obj) >1:
                    raise except_orm("Thông báo", ("Có nhiều hơn 1 cấu hình trong gửi thông báo. Vui lòng Deactive 1 cấu hình"))
                for a in warehouse_point_send_obj.orderpoint_send_mail_ids:
                    if a.location_id.id == line.id:
                        partner_ids = [(4, x) for x.partner_id in a.user_ids]
                date_start = datetime.now()
                date_start = date_start.replace(minute=50, hour=3, second=0)
                stop = date_start.replace(minute=30, hour=7, second=0)
                alarm_ids = self.env['calendar.alarm'].search([('id', '=', '3')])
                calender_id = self.env['calendar.event'].create({
                    'name': 'V/v Hết hàng',
                    'partner_ids': [(4, x) for x in partner_ids],
                    'start_datetime': date_start,
                    'duration': 4,
                    'alarm_ids': [(4, x.id) for x in alarm_ids],
                    'start': date_start,
                    'stop': stop,
                    'description': body_mail,
                })
                # mail_obj = self.env['mail.mail']
                # vals = {
                #     'subject': 'V/v Hết hàng',
                #     'email_form': 'lesang26061995@gmail.com',
                #     'email_to': 'lesang2606@gmail.com',
                #     'email_cc': 'sangla@izisolution.vn',
                #     'body_html': str(body_mail)
                # }
                # mail_obj.create(vals).send()
                # _logger.error('Khách hàng không tồn tại trong hệ thống')
            # hết


class StockJobWarehouseOderpointSendMailLine(models.Model):
    _name = 'stock.warehouse.orderpoint.send.mail.line'

    location_id = fields.Many2one('stock.location', "Location")
    user_ids = fields.Many2many('res.user', "User")
    orderpoint_send_mail_id = fields.Many2one('stock.warehouse.orderpoint.send.mail', "Send Mail")
