# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import except_orm, UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    department_rate_line_ids = fields.One2many('department.rate.line', 'partner_id', string='Department Rate Line')

