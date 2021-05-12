# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError, MissingError


class TherapyRecordProductUpdate(models.Model):
    _name = 'therapy.record.product.update'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    therapy_record_id = fields.Many2one('therapy.record', string='Therapy record')
    user_id = fields.Many2one('res.users', string='User', track_visibility='onchange')
    date_update = fields.Datetime(string='Date update', default=lambda self: fields.Datetime.now(), track_visibility='onchange')
    update_line_ids = fields.One2many('therapy.record.product.update.line', 'product_update_id', string='Therapy Record Product Update Line')

    @api.onchange('therapy_record_id')
    def onchange_therapy_record_id(self):
        print(len(self.therapy_record_id.therapy_record_product_ids))
        self.user_id = self._context.get('default_user_id')
        therapy_record_id = self.env['therapy.record'].search([('id', '=', self._context.get('default_therapy_record_id'))], limit=1)
        if therapy_record_id:
            arr_product = []
            for record_product_id in therapy_record_id.therapy_record_product_ids:
                arr_product.append({
                    'product_update_id': self.id,
                    'order_id': record_product_id.order_id.id,
                    'order_line_id': record_product_id.order_line_id.id,
                    'product_id': record_product_id.product_id.id,
                    'uom_id': record_product_id.uom_id.id,
                    'price_unit': record_product_id.price_unit,
                    'qty_max_old': record_product_id.qty_max,
                    'qty_max_new': record_product_id.qty_max,
                })
            if len(arr_product) <= 0:
                raise UserError('Chưa có sản phẩm dịch vụ tồn trong hồ sơ trị liệu này! Vui lòng kiểm tra lại')
            self.update_line_ids = [(0, 0, product_update) for product_update in arr_product]

    def update_therapy_record_product(self):
        for update_line_id in self.update_line_ids:
            remain_product = self.env['therapy.record.product'].search([('product_id', '=', update_line_id.product_id.id), ('therapy_record_id', '=', update_line_id.product_update_id.therapy_record_id.id), ('order_id', '=', update_line_id.order_id.id), ('order_line_id', '=', update_line_id.order_line_id.id)],order="id desc",limit=1)
            if remain_product:
                if update_line_id.qty_max_old == update_line_id.qty_max_new:
                    update_line_id.unlink()
                    continue
                if remain_product.order_id:
                    remain_product.qty_max = update_line_id.qty_max_new
                else:
                    if update_line_id.qty_max_old == 0:
                        remain_product.qty_max += update_line_id.qty_max_new
                    else:
                        remain_product.qty_max = update_line_id.qty_max_new
                remain_product.price_subtotal_incl = remain_product.qty_max * remain_product.price_unit
            else:
                self.env['therapy.record.product'].create({
                    'therapy_record_id': self.therapy_record_id.id,
                    'product_id': update_line_id.product_id.id,
                    'uom_id': update_line_id.uom_id.id,
                    'qty_used': 0,
                    'qty_max': update_line_id.qty_max_new,
                    # 'body_area_ids': False,
                    # 'order_id': update_line_id.order_id.id,
                    # 'order_line_id': update_line_id.order_line_id.id,
                    'price_unit': update_line_id.price_unit,
                    'price_subtotal_incl': 0,
                })
                # print('remain_product.product_id.name')/



class TherapyRecordProductUpdateLine(models.Model):
    _name = 'therapy.record.product.update.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_qty_max_new(self):
        return self.qty_max_old

    product_update_id = fields.Many2one('therapy.record.product.update', string='Therapy Record Product Update')
    order_id = fields.Many2one('pos.order', string='Order', track_visibility='onchange')
    order_line_id = fields.Many2one('pos.order.line', string='Line Order')
    product_id = fields.Many2one('product.product', string='Product', track_visibility='onchange')
    uom_id = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure', readonly=True)
    price_unit = fields.Float(string='Price Unit')
    qty_max_old = fields.Float(string='Quantity Max Old', track_visibility='onchange')
    qty_max_new = fields.Float(string='Quantity Max New', default=_default_qty_max_new, track_visibility='onchange')
    note = fields.Text(string='Note', track_visibility='onchange')

