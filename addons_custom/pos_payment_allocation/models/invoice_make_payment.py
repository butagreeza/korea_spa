# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from datetime import datetime

class InvoiceMakePayment(models.TransientModel):
    _inherit = 'invoice.make.payment'

    def process_payment(self):
        res = super(InvoiceMakePayment, self).process_payment()
        order_id = self.sudo().env['pos.order'].search([('name', '=', self.invoice_id.reference)])
        if order_id.x_type != '2':
            self.sudo().auto_pos_payment_allocation(self.amount, order_id)
        return res

    def auto_pos_payment_allocation(self, amount, order_id):
        payment_allocaiton = self.env['pos.payment.allocation']
        payment_allocation_line = self.env['pos.payment.allocation.line']
        for order in order_id:
            argvs = {
                'order_id': order.id,
                'date': datetime.today().date(),
                'partner_id': order.partner_id.id,
                'invoice_id': self.invoice_id.id,
                'amount_total': amount,
                'amount_allocation': 0,
                'amount_remain': 0,
                'state': 'draft',
                'default_unlink': True,
            }
            payment_allocaiton_id = payment_allocaiton.create(argvs)
            for line in order.lines.filtered(lambda order_line: order_line.price_subtotal_incl != 0):
                amount_readonly = False
                if line.price_subtotal_incl == 0:
                    amount_readonly = True
                if line.product_id.product_tmpl_id.x_type_card != 'none':
                    continue
                arvgss = {
                    'product_id': line.product_id.id,
                    'quantity': line.qty,
                    'amount': 0,
                    'amount_product': line.price_subtotal_incl,
                    'amount_payment_product': line.x_amount_payment,
                    'payment_allocation_id': payment_allocaiton_id.id,
                    'order_id': order.id,
                    'order_line_id': line.id,
                    'amount_readonly': amount_readonly,
                }
                payment_allocaiton_line_id = payment_allocation_line.create(arvgss)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    pos_payment_ids = fields.One2many('pos.payment.allocation', 'partner_id', string="Order")