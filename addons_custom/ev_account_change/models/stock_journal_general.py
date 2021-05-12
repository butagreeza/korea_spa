# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockJouranlGeneral(models.Model):
    _inherit = 'stock.journal.general'


    change_value = fields.Float('Change Value')

    @api.onchange('change_value')
    def on_change_value(self):
        self.ensure_one()
        self.price_unit = self.change_value / self.qty