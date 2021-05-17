# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, except_orm


class ResPartner(models.Model):
    _inherit = 'res.partner'

    claim_ids = fields.One2many('crm.claim', 'partner_id', string='Claim')
    claim_count = fields.Integer(string='Claim', compute='_compute_claim_ids')

    @api.depends('claim_ids')
    def _compute_claim_ids(self):
        for line in self:
            line.claim_count = len(line.claim_ids)