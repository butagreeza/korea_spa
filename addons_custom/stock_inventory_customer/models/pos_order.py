# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo import time
from odoo.exceptions import except_orm,ValidationError, UserError
from odoo.osv import osv
import xlrd
import xlwt
import base64
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import logging
logger = logging.getLogger(__name__)



class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _update_service_card(self):
        param_obj = self.env['ir.config_parameter']
        code = param_obj.get_param('default_code_exception')
        list = code.split(',')
        lot = self.env['stock.production.lot']
        lot_ids = []
        for line in self.lines:
            if line.product_id.product_tmpl_id.x_type_card == 'tdv':
                lot_obj = lot.search(
                    [('name', '=', line.pack_lot_ids.lot_name), ('product_id', '=', line.product_id.id)])
                lot_ids.append(lot_obj.id)
        if len(lot_ids) != 0:
            lot_obj = lot.search([('id', '=', lot_ids[0])])
            amount, lines_lot, amount_product = self._add_service_to_card(list, lot_obj)
            lot_obj.x_card_detail_ids = lines_lot
            if lot_obj.x_release_id.expired_type == '1':
                date = datetime.strptime(self.date_order, "%Y-%m-%d %H:%M:%S") + relativedelta(
                    months=lot_obj.x_release_id.validity)
                lot_obj.life_date = date.replace(minute=0, hour=0, second=0)
            lot_obj.x_customer_id = self.partner_id.id if not self.x_owner_id else self.x_owner_id.id
            lot_obj.x_status = 'using'
            lot_obj.x_amount = amount
            # lot_obj.x_payment_amount = amount_payment - amount_product
            lot_obj.x_order_id = self.id

    def pos_payment_allocation(self, arr_excel):
        payment_allocaiton = self.env['pos.payment.allocation']
        payment_allocation_line = self.env['pos.payment.allocation.line']
        for order in self:
            amount = 0
            # if order.x_type == '1':
            for statement in order.statement_ids:
                if statement.journal_id.id != self.session_id.config_id.journal_debt_id.id:
                    amount += statement.amount
            destroy_service_id = self.env['pos.destroy.service']
            destroy_service = self.env['pos.destroy.service'].search([('new_order_id', '=', self.id)])
            if destroy_service:
                destroy_service_id = destroy_service.id
            else:
                destroy_service_id = False
            if amount == 0:
                continue
            argvs = {
                'order_id': order.id,
                'date': order.date_order,
                'partner_id': order.partner_id.id,
                'invoice_id': order.invoice_id.id if order.invoice_id else False,
                'amount_total': amount,
                'amount_allocation': amount,
                'amount_remain': 0,
                'state': 'draft',
                'default_unlink': True,
                'destroy_service_id': destroy_service_id,
            }
            payment_allocaiton_id = payment_allocaiton.create(argvs)
            for line in self.lines:
                amount_line = 0
                for row in arr_excel:
                    if row['product_id'] == line.product_id.id and row['qty_total'] == line.qty and row['total_amount_money'] == line.price_subtotal_incl:
                        amount_line = row['payment_amount']
                arvgss = {
                    'product_id': line.product_id.id,
                    'quantity': line.qty,
                    'amount': amount_line,
                    'amount_product': line.price_subtotal_incl,
                    'amount_payment_product': 0,
                    'payment_allocation_id': payment_allocaiton_id.id,
                    'order_id': order.id,
                    'order_line_id': line.id,
                    'amount_readonly': True,
                }
                payment_allocaiton_line_id = payment_allocation_line.create(arvgss)

    def _update_service_card_import(self, arr_excel):
        param_obj = self.env['ir.config_parameter']
        code = param_obj.get_param('default_code_exception')
        list = code.split(',')
        lot = self.env['stock.production.lot']
        lot_ids = []
        for line in self.lines:
            if line.product_id.product_tmpl_id.x_type_card == 'tdt':
                lot_obj = lot.search(
                    [('name', '=', line.pack_lot_ids.lot_name), ('product_id', '=', line.product_id.id)])
                lot_ids.append(lot_obj.id)
        if len(lot_ids) != 0:
            lot_obj = lot.search([('id', '=', lot_ids[0])])
            amount, lines_lot, amount_product = self._add_service_to_card(list, lot_obj)
            for line_lot in lines_lot:
                for line in arr_excel:
                    if line['product_id'] == line_lot['product_id']:
                        line_lot['qty_use'] += line['qty_used']
            lot_obj.x_card_detail_ids = lines_lot
            if lot_obj.x_release_id.expired_type == '1':
                date = datetime.strptime(self.date_order, "%Y-%m-%d %H:%M:%S") + relativedelta(
                    months=lot_obj.x_release_id.validity)
                lot_obj.life_date = date.replace(minute=0, hour=0, second=0)
            lot_obj.x_customer_id = self.partner_id.id if not self.x_owner_id else self.x_owner_id.id
            lot_obj.x_status = 'using'
            lot_obj.x_amount = amount
            # lot_obj.x_payment_amount = amount_payment - amount_product
            lot_obj.x_order_id = self.id

    def _get_service_card(self):
        ProductionLotObj = self.env['stock.production.lot']
        ProductObj = self.env['product.product']
        if self._context.get('inventory_therapy'):
            code_product_service_card = 'TDT'
        else:
            code_product_service_card = 'TDV'
        product = ProductObj.search([('default_code', '=', code_product_service_card)], limit=1)
        if not product: raise except_orm('Thông báo',
                                         'Chưa có sản phẩm là Thẻ dịch vụ[%s]. Vui lòng cấu hình trước khi bán dịch vụ.' % (
                                             str(code_product_service_card)))

        if not self.session_id.config_id.x_card_picking_type_id: raise except_orm('Thông báo',
                                                                                  'Chưa cấu hình loại dịch chuyển của thẻ dịch vụ cho điểm bán hàng %s.' % (
                                                                                  self.session_id.config_id.name,))
        if not self.session_id.config_id.x_card_picking_type_id.default_location_src_id: raise except_orm('Thông báo',
                                                                                                          'Loại dịch chuyển của thẻ dịch vụ của điểm bán hàng %s chưa chọn địa điểm nguồn mặc định.' % (
                                                                                                          self.session_id.config_id.name,))
        location = self.session_id.config_id.x_card_picking_type_id.default_location_src_id

        query = ''' SELECT a.id FROM stock_production_lot a, izi_product_release b
                            WHERE a.x_release_id = b.id and b.product_id = %s AND b.location_id = %s
                            AND b.state = %s AND a.x_status = %s AND
                            ((a.life_date is not null and a.life_date >= now()) OR a.life_date is null) 
                            and not exists (select 1 from pos_order_line where lot_name = a.name)
                            ORDER BY a.create_date LIMIT 1 for update nowait'''
        # print(query % (product.id, location.id, 'done', 'actived', ) )
        self._cr.execute(query, (product.id, location.id, 'done', 'actived',))
        res = self._cr.dictfetchone()
        if not res: raise except_orm('Thông báo',
                                     'Đã hết %s trong kho [%s]%s. Liên hệ quản lý để phát hành thêm trước khi bán.' % (str(product.name),
                                     str(location.x_code), str(location.name),))
        service_card = ProductionLotObj.search([('id', '=', res['id'])])
        service_card.update({'x_status': 'using'})

        return service_card