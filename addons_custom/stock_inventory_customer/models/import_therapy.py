# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockInventoryCustomerUpdateTherapy(models.Model):
    _name = 'stock.inventory.customer.update.therapy'

    inventory_id = fields.Many2one('stock.inventory.customer.update',string='Update Inventory')
    partner_id = fields.Many2one('res.partner', 'Customer')
    therapy_id = fields.Many2one('therapy.record', string='Therapy Record')
    product_id = fields.Many2one('product.product','Service')
    total_qty = fields.Integer('Qty total')
    qty_hand = fields.Integer('Qty hand')
    qty_use = fields.Integer('Qty used')
    total_amount_money = fields.Float('Amount total')
    payment_amount = fields.Float('Amount payment')
    debt = fields.Float('Amount debt')
    order_id = fields.Many2one('pos.order')
    body_area_ids = fields.Many2many('body.area', string='Body Area')
    note = fields.Char("Note")

class TransferFileTherapy(models.Model):
    _name = 'transfer.file.therapy'

    partner_id = fields.Char(string='partner')
    partner_name = fields.Char(string='partner name')
    phone = fields.Char(string='phone')
    phone_x = fields.Char(string='phone_x')
    birthday = fields.Char(string='birthday')
    product_code = fields.Char(string='product_code')
    product_name = fields.Char(string='product_name')
    product_include = fields.Char(string='product_include')
    total_product = fields.Char(string='total_product')
    total_product_used = fields.Char(string='total_product_used')
    massage_actual = fields.Char(string='massage_actual')
    total_amount = fields.Char(string='total_amount')
    total_payment = fields.Char(string='total_payment')
    total_paid = fields.Char(string='total_paid')
    product_note = fields.Char(string='product_note')
    date_update = fields.Char(string='date_update')
    inventory_id = fields.Many2one('stock.inventory.customer.update', string='Update Inventory')