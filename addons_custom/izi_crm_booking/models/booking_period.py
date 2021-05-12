# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, except_orm
import logging

_logger = logging.getLogger(__name__)


class BookingPeriod(models.Model):
    _name = 'booking.period'

    name = fields.Char(string='Name')
    from_time = fields.Float(string='From time')
    to_time = fields.Float(string='To Time')

    @api.model
    def create(self, vals):
        if vals.get('from_time') >= vals.get('to_time'):
            raise except_orm('Cảnh báo!', ('Thời gian bắt đầu phải nhỏ hơn thời gian kết thúc!'))
        booking_periods = self.env['booking.period'].search([('id', '!=', 0)])
        for bp in booking_periods:
            if round(bp.from_time, 6) <= round(vals.get('from_time'), 6) <= round(bp.to_time, 6) or round(bp.from_time, 6) <= round(vals.get('to_time'), 6) <= round(bp.to_time, 6) or round(vals.get('from_time'), 6) <= round(bp.from_time, 6) <= round(vals.get('to_time'), 6) or round(vals.get('from_time'), 6) <= round(bp.to_time, 6) <= round(vals.get('to_time'), 6):
                raise except_orm('Cảnh báo!', ('Khung giờ bạn vừa nhập không đồng nhất với khung giờ %s' % bp.name))
        return super(BookingPeriod, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(BookingPeriod, self).write(vals)
        if self.from_time >= self.to_time:
            raise except_orm('Cảnh báo!', ('Thời gian bắt đầu phải nhỏ hơn thời gian kết thúc!'))
        booking_periods = self.env['booking.period'].search([('id', '!=', 0)])
        for bp in booking_periods:
            if (round(bp.from_time, 6) <= round(self.from_time, 6) <= round(bp.to_time, 6) or round(bp.from_time, 6) <= round(self.to_time, 6) <= round(bp.to_time, 6) or round(self.from_time, 6) <= round(bp.from_time, 6) <= round(self.to_time, 6) or round(self.from_time, 6) <= round(bp.to_time, 6) <= round(self.to_time, 6)) and bp.id != self.id:
                raise except_orm('Cảnh báo!', ('Khung giờ bạn vừa nhập không đồng nhất với khung giờ %s' % bp.name))
        return res

