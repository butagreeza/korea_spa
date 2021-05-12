# -*- coding: utf-8 -*-
from odoo import models, api, fields , _
from odoo.exceptions import except_orm
from odoo.osv import expression

class ResPartnerCustom(models.Model):
    _inherit = 'res.partner'

    deposit_line_ids = fields.One2many('pos.customer.deposit.line', 'partner_id', string="Destroy Service")
    deposit_count = fields.Integer(string='Deposit', compute='get_count_deposit')

    @api.depends('deposit_count')
    def get_count_deposit(self):
        for detail in self:
            detail.deposit_count = len(detail.deposit_line_ids)