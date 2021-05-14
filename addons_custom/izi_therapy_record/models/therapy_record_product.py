# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError, MissingError


class TherapyRecordProduct(models.Model):
    _name = 'therapy.record.product'

    name = fields.Char('Therapy record product')
    therapy_record_id = fields.Many2one('therapy.record', string='Therapy Record')
    product_id = fields.Many2one('product.product', string='Product')
    uom_id = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure', readonly=True)
    qty_used = fields.Float(string='Quantity Used')
    qty_available = fields.Float(string='Quantity available', compute='_compute_qty_available')
    qty_max = fields.Float(string='Quantity Max')
    note = fields.Char(string='Note')
    body_area_ids = fields.Many2many('body.area', string='Body Area')
    order_id = fields.Many2one('pos.order', string='Order')
    order_line_id = fields.Many2one('pos.order.line', string='Line Order')
    price_unit = fields.Float(string='Price Unit')
    price_subtotal_incl = fields.Float(string='Price Total')
    amount_paid = fields.Float(string='Amount Paid', compute='_compute_qty_available', store=False)
    amount_used = fields.Float(string='Amount Used', compute='_compute_qty_available', store=True)
    actual_debt = fields.Float(string='Actual Debt', compute='_compute_qty_available', store=True)
    payment_allocation_ids = fields.One2many('pos.payment.allocation', related='order_id.x_pos_payment_ids', string='Payment Allocation', readonly=True)

    @api.depends('qty_used', 'qty_max', 'price_unit', 'payment_allocation_ids.state')
    def _compute_qty_available(self):
        Payment_allocationself_Obj = self.env['pos.payment.allocation']
        Order_Obj = self.env['pos.order']
        for product in self:
            product.qty_available = product.qty_max - product.qty_used
            if product.price_unit:
                product.amount_used = product.price_unit * product.qty_used
            amount = 0
            order_ids = Order_Obj.search(['|',('id', '=', product.order_id.id), ('x_pos_partner_refund_id', '=', product.order_id.id)])
            payment_allocation_ids = Payment_allocationself_Obj.search([('order_id', 'in', order_ids.ids), ('state', '=', 'done')])
            for payment_allocation in payment_allocation_ids:
                for line_allocation in payment_allocation.payment_allocation_ids:
                    if line_allocation.product_id.id == product.product_id.id and line_allocation.order_line_id.id == product.order_line_id.id:
                        amount += line_allocation.amount
            product.amount_paid = amount
            product.actual_debt = product.amount_used - product.amount_paid
