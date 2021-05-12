# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, datetime
from odoo.exceptions import except_orm, UserError, MissingError, ValidationError


class PosUseMaterial(models.Model):
    _inherit = 'pos.user.material'

    merge_service_id = fields.Many2one('merge.use.service', "Merge Servic")
