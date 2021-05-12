# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError

class ProductCategory(models.Model):
    _inherit = 'product.category'

    x_is_use_barem = fields.Boolean(string="Is use barem", default=False)
    x_is_therapy_record = fields.Boolean(string="Is therapy record", default=False)

class ProductProduct(models.Model):
    _inherit = 'product.product'


    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        products = super(ProductProduct, self).name_search(name, args, operator, limit)
        categ_id = self._context.get('categ_id', False)
        if categ_id:
            products = self.search(['|', ('default_code', '=', name), ('name', 'ilike', name), ('categ_id', '=', self._context['categ_id']), ('available_in_pos', '=', True)]).name_get()
        component_id = self._context.get('component_id', False)
        if component_id:
            options = self.env['therapy.bundle.barem.option'].search([('component_id', '=', component_id)])
            arr_product_id = []
            for option in options:
                arr_product_id.append(option.product_id.id)
            products = self.search([('id', 'in', arr_product_id)]).name_get()
        return products


class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_is_massage = fields.Boolean('Is Massage', default=False)
    x_is_injection = fields.Boolean('Is Injection', default=False)
