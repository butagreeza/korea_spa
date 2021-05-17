# -*- coding: utf-8 -*-
from reportlab.graphics.barcode.common import Barcode

from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from odoo.exceptions import except_orm, ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import math
import copy


class ServiceCardUsing(models.Model):
    _inherit = "izi.service.card.using"

    @api.multi
    def action_search_serial(self):
        self.service_card_ids.unlink()
        serial = self.serial_code
        if serial and len(serial) > 0:
            serial = str(self.serial_code).upper().strip()
        else:
            raise except_orm(_('Thông báo'), _('Vui lòng nhập mã thẻ !'))
        lot_obj = self.env['stock.production.lot'].search([('name', '=', serial)], limit=1)
        if lot_obj:
            if lot_obj.x_status != 'using':
                raise except_orm('Cảnh báo!', "Thẻ không dùng được")
            customer_obj = lot_obj.x_customer_id
            date = datetime.strptime(lot_obj.life_date, '%Y-%m-%d %H:%M:%S') + timedelta(days=1)
            date_life = date.date()
            if date_life <= datetime.strptime(self.redeem_date, '%Y-%m-%d %H:%M:%S').replace(minute=0, hour=0,
                                                                                             second=0).date():
                raise except_orm('Cảnh báo!', ('Thẻ đã hết hạn'))
            if lot_obj.x_status != 'using' and lot_obj.x_status != 'used':
                raise except_orm('Cảnh báo!', ('Thẻ không hợp lệ'))
            lines = []
            for line in lot_obj.x_card_detail_ids:
                if line.total_qty == line.qty_use:
                    continue
                if line.state == 'ready':
                    if line.body_area_ids:
                        for body_id in line.body_area_ids:
                            argvs = {
                                'serial_id': lot_obj.id,
                                'detail_serial_id': line.id,
                                'service_id': line.product_id.id,
                                'paid_count': line.total_qty,
                                'used_count': line.qty_use,
                                'uom_id': line.product_id.uom_id.id,
                                'type': 'service_card',
                                'body_area_ids': [(6, 0, [body_id.id])],
                            }
                            lines.append(argvs)
                    else:
                        argvs = {
                            'serial_id': lot_obj.id,
                            'detail_serial_id': line.id,
                            'service_id': line.product_id.id,
                            'paid_count': line.total_qty,
                            'used_count': line.qty_use,
                            'uom_id': line.product_id.uom_id.id,
                            'type': 'service_card',
                        }
                        lines.append(argvs)

            # self.service_card_ids = lines
        else:
            if not self.pos_session_id.branch_id.brand_id: raise except_orm('Thông báo',
                                                                            'Chi nhánh %s của bạn chưa gắn thương hiệu không thể tìm KH' % (
                                                                                str(
                                                                                    self.pos_session_id.branch_id.name)))
            customer_obj = self.env['res.partner'].search(
                ['|', '|', '|', ('x_code', '=', serial.upper().strip()), ('x_old_code', '=', serial.upper().strip()),
                 ('phone', '=', serial.upper().strip()), ('mobile', '=', serial.upper().strip()),
                 ('x_brand_id', '=', self.pos_session_id.branch_id.brand_id.id)])
            if customer_obj:
                lot_ids = self.env['stock.production.lot'].search([('x_customer_id', '=', customer_obj.id)])
                if not lot_ids:
                    raise except_orm("Cảnh báo",
                                     ("Không tìm thấy dịch vụ của khách hàng. VUi lòng kiểm tra lại mã khách hàng"))
                lines = []
                for line in lot_ids:
                    date = datetime.strptime(line.life_date, '%Y-%m-%d %H:%M:%S') + timedelta(days=1)
                    date_life = date.date()
                    if date_life <= datetime.strptime(self.redeem_date, '%Y-%m-%d %H:%M:%S').replace(minute=0, hour=0,
                                                                                                     second=0).date():
                        continue
                    if line.x_release_id.use_type == '0' and line.x_customer_id.id != customer_obj.id:
                        continue
                    if line.x_status == 'destroy':
                        continue
                    for tmp in line.x_card_detail_ids:
                        if tmp.total_qty == tmp.qty_use:
                            continue
                        if tmp.state == 'ready':
                            if line.body_area_ids:
                                for body_id in line.body_area_ids:
                                    argvs = {
                                        'type': 'service_card',
                                        'serial_id': line.id,
                                        'detail_serial_id': tmp.id,
                                        'service_id': tmp.product_id.id,
                                        'paid_count': tmp.total_qty,
                                        'used_count': tmp.qty_use,
                                        'uom_id': tmp.product_id.product_tmpl_id.uom_id.id,
                                        'body_area_ids': [(6, 0, [tmp.body_id.id])],
                                    }
                                    lines.append(argvs)
                            else:
                                argvs = {
                                    'type': 'service_card',
                                    'serial_id': line.id,
                                    'detail_serial_id': tmp.id,
                                    'service_id': tmp.product_id.id,
                                    'paid_count': tmp.total_qty,
                                    'used_count': tmp.qty_use,
                                    'uom_id': tmp.product_id.product_tmpl_id.uom_id.id,
                                }
                                lines.append(argvs)
                if len(lines) == 0:
                    raise except_orm('Cảnh báo!', ("Thẻ dịch vụ của khách hàng đã hết!"))
                # self.service_card_ids = lines
                # self.customer_id = customer_obj.id
                # self.rank_id = customer_obj.x_rank.id
                # self.pricelist_id = customer_obj.property_product_pricelist.id
            else:
                raise except_orm('Cảnh báo!', ("Mã không được tìm thấy. Vui lòng kiểm tra lại"))
        check_body = False
        for line in self.lines:
            if line.service_id.x_is_massage or line.service_id.x_is_injection:
                check_body = True
        self.is_body_area = True
        self.service_card_ids = lines
        self.customer_id = customer_obj.id
        self.rank_id = customer_obj.x_rank.id
        self.pricelist_id = customer_obj.property_product_pricelist.id
        self.serial_code = ''
        self.partner_search_id = ''


    def _check_service_card_ids_service_card1_ids(self):
        arr_product = []
        total = 0
        total_use = 0
        DetailServiceCard = self.env['izi.service.card.detail']
        for service_card in self.service_card_ids:
            if service_card.quantity == 0:
                service_card.unlink()
            if service_card.body_area_ids and self.type == 'card':
                arr_product.append(service_card.service_id.id)
            else:
                if (len(service_card.employee_ids) + len(service_card.doctor_ids)) == 0:
                    raise except_orm('Cảnh báo!', ('Bạn cần chọn kỹ thuật viên trước khi xác nhận'))
                if service_card.service_id.x_use_doctor and not service_card.doctor_ids and service_card.quantity != 0:
                    raise except_orm('Cảnh báo!', 'Dịch vụ [%s]%s phải chọn bác sĩ!' % (
                    str(service_card.service_id.default_code), str(service_card.service_id.name)))
        # kiểm tra xem tổng số buổi sử dụng có lớn hơn số lần mua không
        for product_id in arr_product:
            detail_service_id = DetailServiceCard.search([('product_id', '=', product_id), ('lot_id', '=', self.service_card_ids[0].serial_id.id)])
            for service_card in self.service_card_ids.filtered(lambda line:line.service_id.id == product_id):
                total_use += service_card.quantity
            qty_used = total_use + detail_service_id.qty_use
            if qty_used > detail_service_id.total_qty:
                raise UserError('Tổng số lượng sử dụng: %s đang lớn hơn số lượng mua: %s ' % (qty_used, detail_service_id.total_qty))
        for service_card1 in self.service_card1_ids:
            if service_card1.quantity == 0:
                service_card1.unlink()
            else:
                if (len(service_card1.employee_ids) + len(service_card1.doctor_ids)) == 0:
                    raise except_orm('Cảnh báo!', ('Bạn cần chọn kỹ thuật viên trước khi xác nhận'))
                if service_card1.service_id.x_use_doctor and not service_card1.doctor_ids and service_card1.quantity != 0:
                    raise except_orm('Cảnh báo!', 'Dịch vụ [%s]%s phải chọn bác sĩ!' % (
                    str(service_card1.service_id.default_code), str(service_card1.service_id.name)))


