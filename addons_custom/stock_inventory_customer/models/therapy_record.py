# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TherapyRecord(models.Model):
    _inherit = 'therapy.record'

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     args = args or []
    #     domain = []
    #     res = super(TherapyRecord, self).name_search(name, args, operator, limit)
    #     partner_id = self.env.context.get('partner_id')
    #     categ_id = self.env.context.get('categ_id')
    #
    #     if partner_id and categ_id:
    #         partner = self.env['therapy.record'].search([('partner_id', '=', partner_id), ('categ_id', '=', categ_id)])
    #         res = partner.name_get()
    #
    #     return res
