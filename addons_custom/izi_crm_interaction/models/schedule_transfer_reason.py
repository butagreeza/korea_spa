# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from datetime import datetime
from dateutil.relativedelta import relativedelta

import logging

class ScheduleTransferReason(models.Model):
    _name = 'schedule.transfer.reason'

    name = fields.Char(string='Name')

    @api.model_cr
    def init(self):
        reason_id = self.search([])
        if not reason_id:
            self.create({'name': 'trùng lịch'})
            self.create({'name': 'khách hàng đặc biệt'})
            self.create({'name': 'đặt lịch khác'})
            self.create({'name': 'khách không cần chăm sóc'})
            self.create({'name': 'đã được tương tác'})
        sup = super(ScheduleTransferReason, self)

