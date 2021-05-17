# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta

class IziServiceCardDetail(models.Model):
    _inherit = 'izi.service.card.detail'

    body_area_ids = fields.Many2many('body.area', string='Body Area')