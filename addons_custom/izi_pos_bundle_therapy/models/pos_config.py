# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError


class PosOrder(models.Model):
    _inherit = 'pos.config'

    x_is_sign_order = fields.Boolean(default=False, string='Sign Order')