# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm

class PosPaymentAllocationLine(models.Model):
    _name = 'pos.payment.allocation.line'

    product_id = fields.Many2one("product.product", "Product")
    quantity  = fields.Float("Quantity")
    amount = fields.Float("Amount") # Số tiền phân bổ trong thanh toán
    amount_product = fields.Float("Amount Product") # Số tiền cần thanh toán cho sản phẩm
    amount_payment_product = fields.Float("Amount Payment Product") # Số tiền đẫ thanh toán
    payment_allocation_id = fields.Many2one('pos.payment.allocation', "Payment Allocation")
    order_id = fields.Many2one('pos.order', "Order")
    order_line_id = fields.Many2one('pos.order.line', "Order Line")
    amount_readonly = fields.Boolean("Amount Readonly", default=False)


    @api.onchange('amount')
    def onchange_amount(self):
        if abs(self.amount) + abs(self.amount_payment_product) > abs(self.amount_product):
            raise except_orm("Cảnh báo!", ("Số tiền phân bổ không thể lớn hơn số tiền của sản phẩm(dịch vụ). %s + %s > %s" % (str(self.amount), str(self.amount_payment_product), str(self.amount_product))))
