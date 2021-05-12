# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ServiceCarDetail(models.Model):
    _inherit = 'izi.service.card.detail'

    amount_payment = fields.Float("Amount Payment")
