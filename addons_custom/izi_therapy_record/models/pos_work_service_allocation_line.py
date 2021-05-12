# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PosWorkServiceAllocationLine(models.Model):
    _inherit = "pos.work.service.allocation.line"

    body_area_ids = fields.Many2many('body.area', string='Body Area')
