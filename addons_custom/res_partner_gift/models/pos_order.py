# -*- coding: utf-8 -*-
from odoo import models, api, fields , _
from odoo.exceptions import except_orm, ValidationError, UserError
from odoo.osv import expression
from odoo import sys, os
import base64, time
from os.path import  join
from datetime import datetime,date
import logging, re
from odoo import http
from odoo.osv.orm import setup_modifiers
from dateutil.relativedelta import relativedelta


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.onchange('product_id', 'qty')
    def _onchange_product_qty(self):
        for line in self:
            if line.product_id.product_tmpl_id.x_type_card in ('tdv', 'pmh') and line.qty != 1:
                raise except_orm('Cảnh báo!',
                                 ('Bạn chỉ có thể bán thẻ dịch vụ, phiếu mua hàng với số lượng là 1 trên 1 dòng'))
            if line.qty == 0:
                raise except_orm('Cảnh báo!',
                                 ('Bạn chỉ có thể bán sản phẩm với số lượng khác 0 trên 1 dòng'))
            if line.product_id and line.product_id.default_code != 'COIN' and line.product_id.product_tmpl_id.x_type_card != 'pmh':
                # line.price_unit = 0
                if line.product_id.type != 'service':
                    total_availability = self.env['stock.quant']._get_available_quantity(line.product_id,
                                                                                         line.order_id.location_id)
                    warning_mess = {
                        'title': _('Cảnh báo!'),
                        'message': _('Sản phẩm "' + str(
                            line.product_id.product_tmpl_id.name) + '" đang có số lượng tồn kho là ' + str(
                            total_availability)) + ' đơn vị sản phẩm.'
                    }
                    if line.qty > total_availability:
                        return {'warning': warning_mess}

    @api.multi
    def action_send_payment(self):
        ProductLot_Obj = self.env['stock.production.lot']
        PosOrderLine = self.env['pos.order.line']
        time_now = datetime.now()
        super(PosOrder, self).action_send_payment()
        for order in self:
            for order_line in order.lines:
                if order_line.product_id.product_tmpl_id.x_type_card == 'pmh':
                    product_lot_ids = ProductLot_Obj.search(
                        [('x_status', '=', 'actived'), ('product_id', '=', order_line.product_id.id)])
                    for product_lot_id in product_lot_ids:
                        check_lot = PosOrderLine.search([('lot_name', '=', product_lot_id.name.upper().strip())])
                        if len(check_lot) != 0:
                            continue
                        order_line.update({
                            'lot_name': product_lot_id.name.upper().strip(),
                        })
                        argvs_lot = {
                            'pos_order_line_id': order_line.id,
                            'lot_name': product_lot_id.name.upper().strip(),
                        }
                        pos_lot_id = self.env['pos.pack.operation.lot'].create(argvs_lot)
                        break
                    if not order_line.lot_name:
                        raise UserError('Không đủ mã Voucher để hoàn thành đơn hàng! Vui lòng phát hành thêm để hoàn thành đơn hàng')

    @api.multi
    def action_order_confirm(self):
        ProductLot_Obj = self.env['stock.production.lot']
        ProductGift_Obj = self.env['partner.gift']
        time_now = datetime.now()
        super(PosOrder, self).action_order_confirm()
        for order in self:
            for order_line in order.lines:
                if order_line.lot_name and order_line.product_id.product_tmpl_id.x_type_card == 'pmh':
                    lot_obj = ProductLot_Obj.search([('name', '=', order_line.lot_name.upper().strip())], limit=1)
                    if not lot_obj:
                        raise UserWarning('Không tìm thấy mã %s' %lot_obj.name)
                    ProductGift_Obj.create({
                        'gift_id': lot_obj.id,
                        'partner_id': order.partner_id.id,
                        'pos_order_id': order.id,
                    })


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    @api.onchange('product_id', 'qty')
    def _onchange_product_qty(self):
        for line in self:
            if line.product_id.product_tmpl_id.x_type_card in ('tdv', 'pmh') and line.qty != 1:
                raise except_orm('Cảnh báo!',
                                 ('Bạn chỉ có thể bán thẻ dịch vụ, phiếu mua hàng với số lượng là 1 trên 1 dòng'))
            if line.qty == 0:
                raise except_orm('Cảnh báo!',
                                 ('Bạn chỉ có thể bán sản phẩm với số lượng khác 0 trên 1 dòng'))
            if line.product_id and line.product_id.default_code != 'COIN' and line.product_id.product_tmpl_id.x_type_card != 'pmh':
                # line.price_unit = 0
                if line.product_id.type != 'service':
                    total_availability = self.env['stock.quant']._get_available_quantity(line.product_id,
                                                                                         line.order_id.location_id)
                    warning_mess = {
                        'title': _('Cảnh báo!'),
                        'message': _('Sản phẩm "' + str(
                            line.product_id.product_tmpl_id.name) + '" đang có số lượng tồn kho là ' + str(
                            total_availability)) + ' đơn vị sản phẩm.'
                    }
                    if line.qty > total_availability:
                        return {'warning': warning_mess}

