# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import models, fields, api

class StockPickingCancel(models.Model):
    _inherit = 'mrp.unbuild'

    @api.multi
    def action_cancel_unbuild(self):
        for res in self:
            for move in res.consume_line_ids:
                move._action_cancel()
            for move_line in res.produce_line_ids:
                move_line._action_cancel()
            res.write({'state': 'draft'})