# -*- coding: utf-8 -*-
from odoo import models, api, fields, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    x_agent_phone = fields.Char(string="Agent Phone")
    x_agent_phone_old = fields.Char(string="Agent Phone Old")