# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, UserError
from datetime import datetime

class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = super(PosOrder, self).name_search(name, args=args, operator=operator, limit=limit)
        if self._context.get('no_refund'):
            order_ids = self.env['pos.order'].search([('x_pos_partner_refund_id', '!=', False)])
            if order_ids:
                arr_order_refund = []
                for order_id in order_ids:
                    arr_order_refund.append(order_id.x_pos_partner_refund_id.id)
                    arr_order_refund.append(order_id.id)
                order_refund_ids = self.browse(arr_order_refund)
                pos_order_ids = self.search([('name', operator, name), ('state', 'in', ['done', 'invoiced']), ('id', 'not in', order_refund_ids.ids), ('partner_id', '=', self._context.get('partner_id'))])
                return pos_order_ids.name_get()
            else:
                return res
        else:
            return res