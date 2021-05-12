# -*- coding: utf-8 -*-
from odoo import models, api, fields , _
from odoo.exceptions import except_orm, ValidationError, UserError
from odoo.osv import expression
from odoo import sys, os
import base64, time
from os.path import  join
from datetime import datetime,date
import logging, re
from odoo import http
from odoo.osv.orm import setup_modifiers
from dateutil.relativedelta import relativedelta


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    x_paid_vc = fields.Boolean(string='Paid by Voucher', default=False)


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    x_vc_id = fields.Many2one('stock.production.lot', string='Voucher lot')
    x_vc_code = fields.Char(related='x_vc_id.name', string='Voucher lot code')
    x_vc_amount = fields.Float(related='x_vc_id.product_id.x_amount', string='Amount Voucher')

    def compute_amount_by_vc(self, order):
        order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
        amount_payment = order.amount_total - order.amount_paid
        if self.x_vc_id and self.x_vc_code:
            amount_vc = 0
            amount = amount_payment
            amount_vc_total = self.x_vc_id.product_id.x_amount
            amount_order_total = 0
            amount_pay_vc = 0
            self.x_vc_id._invalidate_vc_code(order.partner_id.id)
            check_vc_used = self.env['account.bank.statement.line'].search([('x_vc_id', '=', self.x_vc_id.id)])
            amount_bank_payment_ids = self.env['account.bank.statement.line'].search(
                [('pos_statement_id', '=', order.id)])
            amount_vc_used = 0
            for amount_bank_payment_id in amount_bank_payment_ids:
                if amount_bank_payment_id.x_vc_id and amount_bank_payment_id.x_vc_id.product_id.id == self.x_vc_id.product_id.id:
                    amount_vc_used += amount_bank_payment_id.amount
            if self.x_vc_id.product_id.x_type_voucher == 'value':
                if self.x_vc_id.product_id.x_product_card_id:
                    amount = 0
                    for order_line in order.lines:
                        if self.x_vc_id.product_id.x_product_card_id.id == order_line.product_id.id:
                            amount_order_total += order_line.price_subtotal_incl
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
                for line_order in order.lines:
                    for product_vc in self.x_vc_id.product_id.x_product_voucher_ids:
                        if product_vc.product_vc_id.id == line_order.product_id.id:
                            if product_vc.qty < line_order.qty:
                                qty = product_vc.qty
                            else:
                                qty = line_order.qty
                            amount_vc += qty * line_order.price_unit
                amount = amount_vc
        else:
            self.x_vc_id = False
            self.x_vc_code = False
            amount = amount_payment
        return amount


    @api.onchange('x_vc_code')
    def onchange_vc_code(self):
        order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
        amount_payment = order.amount_total - order.amount_paid
        if self.x_vc_id and self.x_vc_code:
            amount_vc = 0
            amount = amount_payment
            amount_vc_total = self.x_vc_id.product_id.x_amount
            amount_order_total = 0
            amount_pay_vc = 0
            #kiểm tra voucher còn khả dụng
            self.x_vc_id._invalidate_vc_code(order.partner_id.id, order.statement_ids.ids)
            check_vc_used = self.env['account.bank.statement.line'].search([('x_vc_id', '=', self.x_vc_id.id)])
            amount_bank_payment_ids = self.env['account.bank.statement.line'].search([('pos_statement_id', '=', order.id)])
            amount_vc_used = 0
            for amount_bank_payment_id in amount_bank_payment_ids:
                if amount_bank_payment_id.x_vc_id and amount_bank_payment_id.x_vc_id.product_id.id == self.x_vc_id.product_id.id:
                    amount_vc_used += amount_bank_payment_id.amount
            if len(check_vc_used) > 0:
                self.x_vc_id = False
                amount = 0
                return {
                    'warning': {
                        'title': _('Cảnh báo'),
                        'message': _('Phiếu mua hàng này đã được sử dụng ở đơn hàng {0}!'.format(check_vc_used.pos_statement_id.name)),
                    }
                }
            #tính toán giá trị voucher được sử dụng
            if self.x_vc_id.product_id.x_type_voucher == 'value':
                if self.x_vc_id.product_id.x_product_card_id:
                    amount = 0
                    for order_line in order.lines:
                        if self.x_vc_id.product_id.x_product_card_id.id == order_line.product_id.id:
                            amount_order_total += order_line.price_subtotal_incl
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
                for line_order in order.lines:
                    for product_vc in self.x_vc_id.product_id.x_product_voucher_ids:
                        if product_vc.product_vc_id.id == line_order.product_id.id:
                            if product_vc.qty < line_order.qty:
                                qty = product_vc.qty
                            else:
                                qty = line_order.qty
                            amount_vc += qty * line_order.price_unit
                amount = amount_vc
        else:
            self.x_vc_id = False
            self.x_vc_code = False
            amount = amount_payment
        return {'value': {
            'amount': amount
        }}


