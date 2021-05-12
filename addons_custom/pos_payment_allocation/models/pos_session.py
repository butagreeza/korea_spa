# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import except_orm


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def action_pos_session_close(self):
        Allocation = self.env['pos.payment.allocation']
        pos_order_ids = self.env['pos.order'].search([('session_id', '=', self.id)])
        for order in pos_order_ids:
            if order.x_type in ('2', '3'):
                continue
            # if len(order.x_pos_payment_ids) == 0:
            #     raise except_orm('Cảnh báo!', (
            #             'Đơn hàng "%s" chưa được phân bổ thanh toán. Vui lòng phân bổ trước khi đóng phiên' % order.name))
            allo = Allocation.search([('order_id', '=', order.id)])
            for a in allo:
                if a.state == 'draft':
                    raise except_orm('Cảnh báo!', (
                            'Đơn phân bổ "%s" chưa đóng. Vui lòng đóng phân bổ' % a.name))
        return super(PosSession, self).action_pos_session_close()