# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from odoo.exceptions import except_orm


class PosOrder(models.Model):
    _inherit = 'pos.order'

    x_pos_payment_line_ids = fields.One2many('pos.payment.allocation.line', 'order_id', string="Order")
    x_pos_payment_ids = fields.One2many('pos.payment.allocation', 'order_id', string="Order")

    @api.multi
    def process_customer_signature(self):
        order = super(PosOrder, self).process_customer_signature()
        if self.x_type != '2':
            self._auto_pos_payment_allocation()
        return order

    # Hàm phân bổ thanh toán cho đơn hàng
    def _auto_pos_payment_allocation(self):
        print(1)
        payment_allocaiton = self.env['pos.payment.allocation']
        payment_allocation_line = self.env['pos.payment.allocation.line']
        for order in self:
            amount = 0
            # if order.x_type == '1':
            for statement in order.statement_ids:
                if statement.journal_id.id != self.session_id.config_id.journal_debt_id.id:
                    amount += statement.amount
            # elif order.x_type == '4':
            #     for line in order.lines:
            #         print("Chưa xử lý trường hợp tạo phân bổ khi hủy dịch vụ")
            # else:
            #     raise except_orm("Cảnh báo!", ("Lỗi trong phân bổ thanh toán. Liên hệ Admin"))
            destroy_service_id = self.env['pos.destroy.service']
            destroy_service = self.env['pos.destroy.service'].search([('new_order_id', '=', self.id)])
            if destroy_service:
                destroy_service_id = destroy_service.id
            else:
                destroy_service_id = False
            if amount == 0:
                continue
            argvs = {
                'order_id': order.id,
                'date': order.date_order,
                'partner_id': order.partner_id.id,
                'invoice_id': order.invoice_id.id if order.invoice_id else False,
                'amount_total': amount,
                'amount_allocation': 0,
                'amount_remain': 0,
                'state': 'draft',
                'default_unlink': True,
                'destroy_service_id': destroy_service_id,
            }
            payment_allocaiton_id = payment_allocaiton.create(argvs)
            amount_allocation = 0
            for line in order.lines.filtered(lambda order_line: order_line.price_subtotal_incl != 0):
                amount_readonly = False
                if line.price_subtotal_incl != 0:
                    if line.order_id.x_type == '4' or line.order_id.x_pos_partner_refund_id:
                        if line.qty > 0:
                            amount_readonly = True
                else:
                    amount_readonly = True
                if line.product_id.product_tmpl_id.x_type_card not in ('none','pmh'):
                    continue
                arvgss = {
                    'product_id': line.product_id.id,
                    'quantity': line.qty,
                    'amount': line.price_subtotal_incl,
                    'amount_product': line.price_subtotal_incl,
                    'amount_payment_product':0,
                    'payment_allocation_id': payment_allocaiton_id.id,
                    'order_id': order.id,
                    'order_line_id': line.id,
                    'amount_readonly': amount_readonly,
                }
                payment_allocaiton_line_id = payment_allocation_line.create(arvgss)
                amount_allocation += line.price_subtotal_incl
            payment_allocaiton_id.update({
                'amount_allocation': amount_allocation
            })


    @api.multi
    def action_run_pos_order_do_tom(self):
        order_obj = self.env['pos.order'].search([('session_id','in',(1,2,48))])



class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    x_amount_payment = fields.Float("Amount Payment") # Số tiền thanh toán cho từng dòng