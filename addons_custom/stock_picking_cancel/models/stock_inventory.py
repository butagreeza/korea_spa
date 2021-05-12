# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockPickingCancel(models.Model):
    _inherit = 'stock.inventory'

    @api.multi
    def action_cancel_inventory(self):
        for res in self:
            for move in res.move_ids:
                move._action_cancel()
            res.write({'state': 'cancel'})