# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HrCustom(models.Model):
    _inherit = 'hr.department'

    # x_owner_id = fields.Many2one('res.partner', "Owner", domain=[('x_shop', '=', True)])
    x_code = fields.Char("Code")
