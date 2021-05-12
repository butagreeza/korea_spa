# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, UserError, MissingError
from datetime import datetime, date as my_date


class DestroyService(models.Model):
    _inherit = 'pos.destroy.service'

    pos_payment_ids = fields.One2many('pos.payment.allocation', 'destroy_service_id', string="Order")

