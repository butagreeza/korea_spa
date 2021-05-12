# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import except_orm, UserError


class DepartmentRateLine(models.Model):
    _name = 'department.rate.line'
    _rec_name = 'department_id'

    department_rate_id = fields.Many2one('department.rate')
    department_id = fields.Many2one('hr.department', string='Department')
    customer_rate = fields.Selection([(0, 'Normal'), (1, 'Good'), (2, "Excellent"), (3, "No rate")], default=3)
    customer_comment = fields.Text("Customer Comment")
    using_id = fields.Many2one('izi.service.card.using', string='Service Using')
    partner_id = fields.Many2one('res.partner', related='department_rate_id.partner_id', string='Partner', readonly=True)
    branch_id = fields.Many2one('res.branch', related='department_rate_id.branch_id', string='Branch', readonly=True)
    rate_time = fields.Datetime(string='Rate Time', related='department_rate_id.rate_time', readonly=True)
