# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _default_brand(self):
        brands = self.env['res.brand'].search([])
        if len(brands) == 1:
            return brands.id
        else:
            return False

    x_brand_id = fields.Many2one("res.brand", "Brand", default=_default_brand)

    _sql_constraints = [
        ('phone_brand_uniq', 'unique(phone, x_brand_id)', 'Partner phone is unique in a brand'),
        ('mobile_brand_uniq', 'unique(mobile, x_brand_id)', 'Partner mobile is unique in a brand'),
    ]