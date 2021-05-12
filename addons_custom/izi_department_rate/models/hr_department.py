# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import except_orm, UserError


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    x_can_be_rate = fields.Boolean(string='Can be rate', default=False)
