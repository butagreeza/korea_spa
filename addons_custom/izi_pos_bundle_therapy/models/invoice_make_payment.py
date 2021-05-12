# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, MissingError, ValidationError, except_orm
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class InvoiceMakePayment(models.TransientModel):
    _inherit = 'invoice.make.payment'

    x_is_sign = fields.Boolean(related="session_id.config_id.x_is_sign_order", string="Is Sign Order", readonly=True)