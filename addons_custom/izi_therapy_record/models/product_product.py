# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import UserError, ValidationError, MissingError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    include_product_id = fields.Many2one('product.product', string='Include Product', domain=[('type', 'in', ['product'])])

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        arr_products = []
        products = super(ProductProduct, self).name_search(name, args, operator, limit)
        # type_id = self._context.get('default_type', False)
        # therapy_record_id = self._context.get('therapy_record_id', False)
        # if type_id == 'warranty':
        #     therapy_record_products = self.env['therapy.record.product'].search([('therapy_record_id', '=', therapy_record_id)])
        #     for therapy_record_product in therapy_record_products:
        #         arr_products.append(therapy_record_product.product_id.id)
        #     products = self.env['product.product'].search([('id', 'in', arr_products)]).name_get()
        if self._context.get('therapy_prescription_id', False):
            prescription_id = self._context.get('therapy_prescription_id', False)
            prescription = self.env['therapy.prescription'].search([('id', '=', prescription_id)])
            therapy_prescription_line_remain_ids = prescription.therapy_prescription_line_remain_ids
            for therapy_prescription_line_remain_id in therapy_prescription_line_remain_ids:
                if therapy_prescription_line_remain_id.product_id.type == 'service':
                    arr_products.append(therapy_prescription_line_remain_id.product_id.id)
            products = self.env['product.product'].search([('id', 'in', arr_products)]).name_get()
        if self._context.get('categ_code', False):
            products = self.env['product.product'].search([('categ_id.x_category_code', '=', self._context.get('categ_code')), ('name', operator, name)]).name_get()
        return products
