# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from odoo.exceptions import except_orm, UserError, MissingError, ValidationError

class PosPaymentService(models.Model):
    _inherit = 'pos.payment.service'

    x_vc_id = fields.Many2one('stock.production.lot', string='Voucher lot')
    x_vc_code = fields.Char(related='x_vc_id.name', string='Voucher lot code')
    x_vc_amount = fields.Float(related='x_vc_id.product_id.x_amount', string='Amount Voucher')

    def compute_amount_by_vc(self, service_card):
        service_card = self.env['izi.service.card.using'].browse(self.env.context.get('active_id', False))
        amount_payment = service_card.payment_amount
        if self.x_vc_id and self.x_vc_code:
            amount_vc = 0
            amount = amount_payment
            amount_vc_total = self.x_vc_id.product_id.x_amount
            amount_order_total = 0
            amount_pay_vc = 0
            self.x_vc_id._invalidate_vc_code(service_card.customer_id.id)
            check_vc_used = self.env['pos.payment.service'].search([('x_vc_id', '=', self.x_vc_id.id)])
            if len(check_vc_used) > 0:
                self.x_vc_id = False
                amount = 0
                return {
                    'warning': {
                        'title': _('Cảnh báo'),
                        'message': _('Phiếu mua hàng này đã được sử dụng ở đơn sử dụng dịch vụ {0}!'.format(check_vc_used.using_service_id.name)),
                    }
                }
            pos_payment_service_ids = self.env['pos.payment.service'].search(
                [('using_service_id', '=', service_card.id)])
            amount_vc_used = 0
            for pos_payment_service_id in pos_payment_service_ids:
                if pos_payment_service_id.x_vc_id and pos_payment_service_id.x_vc_id.product_id.id == self.x_vc_id.product_id.id:
                    amount_vc_used += pos_payment_service_id.amount
            if self.x_vc_id.product_id.x_type_voucher == 'value':
                if self.x_vc_id.product_id.x_product_card_id:
                    amount = 0
                    for service_line in service_card.service_card1_ids:
                        if self.x_vc_id.product_id.x_product_card_id.id == service_line.service_id.id:
                            amount_order_total += service_line.amount
                    amount_order_total -= amount_vc_used
                    # Nếu là Voucher
                    amount_vc = amount_vc_total if amount_vc_total <= amount_order_total else amount_order_total
                    if amount_vc == 0:
                        self.x_vc_id = False
                        amount = 0
                        return {
                            'warning': {
                                'title': _('Cảnh báo'),
                                'message': _('Trên đơn hàng không có hoặc đã được thanh toán hết sản phẩm, dịch vụ nào được '
                                             'cấu hình thanh toán bằng voucher. Vui lòng chọn hình thức thanh toán khác!'),
                            }
                        }
                    if self.x_vc_id.x_discount == 0:
                        amount = amount_payment if amount_payment <= amount_vc else amount_vc
                else:
                    amount = amount_payment if amount_payment <= self.x_vc_id.product_id.x_amount else self.x_vc_id.product_id.x_amount
            else:
                for service_line in service_card.service_card1_ids:
                    for product_vc in self.x_vc_id.product_id.x_product_voucher_ids:
                        if product_vc.product_vc_id.id == service_line.service_id.id:
                            if product_vc.qty < service_line.quantity:
                                qty = product_vc.qty
                            else:
                                qty = service_line.quantity
                            amount_vc += qty * service_line.price_unit
                amount = amount_vc
        else:
            self.x_vc_id = False
            self.x_vc_code = False
            amount = amount_payment
        return amount


    @api.onchange('x_vc_code')
    def onchange_vc_code(self):
        service_card = self.env['izi.service.card.using'].browse(self.env.context.get('active_id', False))
        amount_payment = service_card.payment_amount
        pos_payment_service_ids = self.env['pos.payment.service'].search(
            [('using_service_id', '=', service_card.id)])
        amount_paid = 0
        for pos_payment_service_id in pos_payment_service_ids:
            amount_paid += pos_payment_service_id.amount
        amount_payment -= amount_paid
        if self.x_vc_id and self.x_vc_code:
            amount_vc = 0
            amount = amount_payment
            amount_vc_total = self.x_vc_id.product_id.x_amount
            amount_order_total = 0
            amount_pay_vc = 0
            # self.x_vc_id._invalidate_vc_code(order.customer_id.id, order.statement_ids.ids)
            check_vc_used = self.env['pos.payment.service'].search([('x_vc_id', '=', self.x_vc_id.id)])

            amount_vc_used = 0
            for pos_payment_service_id in pos_payment_service_ids:
                if pos_payment_service_id.x_vc_id and pos_payment_service_id.x_vc_id.product_id.id == self.x_vc_id.product_id.id:
                    amount_vc_used += pos_payment_service_id.amount
            if len(check_vc_used) > 0:
                self.x_vc_id = False
                amount = 0
                return {
                    'warning': {
                        'title': _('Cảnh báo'),
                        'message': _('Phiếu mua hàng này đã được sử dụng ở đơn sử dụng dịch vụ {0}!'.format(check_vc_used.using_service_id.name)),
                    }
                }
            if self.x_vc_id.product_id.x_type_voucher == 'value':
                if self.x_vc_id.product_id.x_product_card_id:
                    amount = 0
                    for service_line in service_card.service_card1_ids:
                        if self.x_vc_id.product_id.x_product_card_id.id == service_line.service_id.id:
                            amount_order_total += service_line.amount
                    amount_order_total -= amount_vc_used
                    # Nếu là Voucher
                    amount_vc = amount_vc_total if amount_vc_total <= amount_order_total else amount_order_total
                    if amount_vc == 0:
                        self.x_vc_id = False
                        amount = 0
                        return {
                            'warning': {
                                'title': _('Cảnh báo'),
                                'message': _('Trên đơn hàng không có hoặc đã được thanh toán hết sản phẩm, dịch vụ nào được '
                                             'cấu hình thanh toán bằng voucher. Vui lòng chọn hình thức thanh toán khác!'),
                            }
                        }
                    if self.x_vc_id.x_discount == 0:
                        amount = amount_payment if amount_payment <= amount_vc else amount_vc
                else:
                    amount = amount_payment if amount_payment <= self.x_vc_id.product_id.x_amount else self.x_vc_id.product_id.x_amount
            else:
                amount_vc = 0
                for service_line in service_card.service_card1_ids:
                    for product_vc in self.x_vc_id.product_id.x_product_voucher_ids:
                        if product_vc.product_vc_id.id == service_line.service_id.id:
                            if product_vc.qty < service_line.quantity:
                                qty = product_vc.qty
                            else:
                                qty = service_line.quantity
                            amount_vc += qty * service_line.price_unit
                amount = amount_vc
        else:
            self.x_vc_id = False
            self.x_vc_code = False
            amount = amount_payment

        return {'value': {
            'amount': amount
        }}
