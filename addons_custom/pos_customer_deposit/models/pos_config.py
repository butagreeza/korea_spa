# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm

class InheritPosConfig(models.Model):
    _inherit = 'pos.config'

    x_allocation_deposit = fields.Boolean(string='Allocation Deposit', default=False, help="Nếu phân bổ doanh thu cho đơn đặt cọc thì PHẢI bỏ hình thức cấn trừ đặt cọc trong mục Phương thức ghi nhân doanh thu")