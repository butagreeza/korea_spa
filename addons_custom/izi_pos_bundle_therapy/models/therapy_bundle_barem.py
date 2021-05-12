# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import UserError, ValidationError, MissingError


class TherapyBundleBarem(models.Model):
    _name = 'therapy.bundle.barem'

    name = fields.Char(string='Therapy bundle Barem')
    value_bundle_max = fields.Float(string='Value Bundle Max')
    value_bundle_min = fields.Float(string='Value Bundle Min')
    therapy_bundle_barem_component_ids = fields.One2many('therapy.bundle.barem.component', 'therapy_bundle_barem_id', string='Bundle Line')
    categ_id = fields.Many2one('product.category', string='Service Category')
    active = fields.Boolean(default=True)
    pos_order_id = fields.Many2one('pos.order', string='Pos Order')

    @api.constrains('value_bundle_max', 'value_bundle_min')
    def _check_value_bundle(self):
        for bundle_barem in self:
            if bundle_barem.value_bundle_min and bundle_barem.value_bundle_max:
                if bundle_barem.value_bundle_min >= bundle_barem.value_bundle_max:
                    raise ValidationError(_('Lỗi khoảng giá trị Barem!'))
                for barem in bundle_barem.env['therapy.bundle.barem'].search([('active', '=', True), ('categ_id', '=', bundle_barem.categ_id.id)]):
                    if barem.value_bundle_min < bundle_barem.value_bundle_min < barem.value_bundle_max or barem.value_bundle_min < bundle_barem.value_bundle_max < barem.value_bundle_max:
                        raise ValidationError(_('Giá trị Barem nhập vào bị trùng với barem khác!'))
                    result_1 = barem.value_bundle_min - bundle_barem.value_bundle_min
                    result_2 = barem.value_bundle_max - bundle_barem.value_bundle_max
                    if result_1 != 0 and result_2 != 0 and (result_2 * result_1) <= 0:
                        raise ValidationError(_('Giá trị Barem nhập vào bị trùng với barem khác!'))


class TherapyBundleBaremLine(models.Model):
    _name = 'therapy.bundle.barem.component'

    name = fields.Char(string='Therapy bundle barem Line')
    qty = fields.Integer(string='Quantity')
    note = fields.Char(string='Note')
    therapy_bundle_barem_id = fields.Many2one('therapy.bundle.barem')
    option_ids = fields.One2many('therapy.bundle.barem.option', 'component_id', string='Option')

    @api.constrains('option_ids')
    def constrain_option_ids(self):
        if not self.option_ids:
            raise UserError('Chưa nhập sản phẩm chi tiết trong %s' %(self.name))


class TherapyBundleBaremOption(models.Model):
    _name = 'therapy.bundle.barem.option'

    name = fields.Char(string='Therapy Bundle Barem Option')
    product_id = fields.Many2one('product.product', string='Product')
    uom_id = fields.Many2one('product.uom',  related='product_id.uom_id', string='Product Unit of Measure', readonly=True)
    component_id = fields.Many2one('therapy.bundle.barem.component', string='Component')