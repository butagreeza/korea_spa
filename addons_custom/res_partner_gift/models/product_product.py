# -*- coding: utf-8 -*-
from odoo import models, api, fields , _
from odoo.exceptions import except_orm, ValidationError
from odoo.osv import expression
from odoo import sys, os
import base64, time
from os.path import  join
from datetime import datetime,date
import logging, re
from odoo import http
from odoo.osv.orm import setup_modifiers
from dateutil.relativedelta import relativedelta

class ProductGift(models.Model):
    _name = 'product.gift'

    name = fields.Char(string='Product Gift')
    product_id = fields.Many2one('product.product', string='Product')
    product_vc_id = fields.Many2one('product.product', string='Product Voucher')
    qty = fields.Float(string='Qty')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_product_card_id = fields.Many2one('product.product', string="Product Card")
    x_product_voucher_ids = fields.One2many('product.gift', 'product_id', string="Product Voucher")
    x_type_voucher = fields.Selection([('value', 'Value'), ('product', 'Product')], string='Type voucher', default='product')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('search_voucher'):
            product_tmpl_ids = self.env['product.template'].search([('x_type_card', '=', 'pmh')])
            recs = self.search([('name', operator, name), ('product_tmpl_id', 'in', product_tmpl_ids.ids)])
            return recs.name_get()
        return super(ProductProduct, self).name_search(name, args=args, operator=operator, limit=limit)

    @api.constrains('x_product_voucher_ids')
    def constrains_x_product_voucher_ids(self):
        for product in self:
            for product_voucher in product.x_product_voucher_ids.filtered(lambda pv: pv.qty <= 0 ):
                product_voucher.unlink()

    @api.constrains('x_type_voucher', 'x_type_card')
    def constrains_x_type_voucher(self):
        if self.x_type_card == 'pmh':
            if self.x_type_voucher == 'value':
                if self.x_amount == 0.0 and self.x_discount == 0.0:
                    raise except_orm('C???nh b??o!', _(
                        "Lo???i th??? l?? phi???u mua h??ng, b???n c???n th??m t???ng ti???n ho???c ph???n tr??m gi???m gi?? cho phi???u n??y!"))
                if self.x_amount < 0.0 and self.x_discount < 0.0:
                    raise except_orm('C???nh b??o!', _(
                        "Lo???i th??? l?? phi???u mua h??ng, t???ng ti???n ho???c ph???n tr??m gi???m gi?? c???a phi???u n??y ph???i l???n h??n 0!"))
            else:
                if not self.x_product_voucher_ids:
                    raise except_orm('C???nh b??o!', _(
                        "Lo???i th??? l?? phi???u mua h??ng, voucher t???ng s???n ph???m kh??ng ???????c ????? tr???ng!"))





