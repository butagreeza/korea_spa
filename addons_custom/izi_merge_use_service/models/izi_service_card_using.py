# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, datetime
from odoo.exceptions import except_orm, UserError, MissingError, ValidationError

class IziServiceCardUsing(models.Model):
    _inherit = 'izi.service.card.using'

    merge_service_id = fields.Many2one('merge.use.service', "Merge Servic")
