# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockPickingCancel(models.Model):
    _inherit = 'stock.picking'


    @api.multi
    def action_cancel_picking(self):
        self.mapped('move_lines')._action_cancel()
        self.write({'is_locked': True})
        return True


    @api.multi
    def action_set_to_draft(self):
        self.write({'state': 'draft'})
        self.mapped('move_lines')._action_set_to_draft()

