# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import except_orm, UserError


class DepartmentRate(models.Model):
    _name = 'department.rate'

    rate_time = fields.Datetime(string='Rate Time')
    partner_id = fields.Many2one('res.partner', string='Customer')
    using_id = fields.Many2one('izi.service.card.using', string='Service Using')
    branch_id = fields.Many2one('res.branch', string='Branch')
    line_ids = fields.One2many('department.rate.line', 'department_rate_id')




