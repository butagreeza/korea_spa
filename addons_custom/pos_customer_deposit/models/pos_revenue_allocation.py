# -*- coding: utf-8 -*-
from werkzeug._internal import _log
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from odoo.exceptions import except_orm, Warning as UserError

class RevenueAllocation(models.Model):
    _inherit = "pos.revenue.allocation"

    pos_customer_deposit_line_id = fields.Many2one('pos.customer.deposit.line', string='Customer Deposit')