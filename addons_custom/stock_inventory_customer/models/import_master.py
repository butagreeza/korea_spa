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
import json
try:
    import cStringIO as stringIOModule
except ImportError:
    try:
        import StringIO as stringIOModule
    except ImportError:
        import io as stringIOModule


class StockInventoryCustomerUpdate(models.Model):
    _name = 'stock.inventory.customer.update'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", default="New", copy=False, track_visibility='onchange')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    type = fields.Selection([('product', 'Product'), ('coin', 'Coin'), ('money', 'Money'), ('therapy', 'Therapy'), ('transfer', 'Transfer')], 'Type',
                            default='product', track_visibility='onchange')
    state = fields.Selection([('draft', 'Draft'), ('updated', 'Updated'), ('done', 'Done'), ('cancel', 'Cancel')], 'State',
                             default='draft', track_visibility='onchange')
    product_ids = fields.One2many('stock.inventory.customer.update.product', 'inventory_id', string='Line')
    coin_ids = fields.One2many('stock.inventory.customer.update.coin', 'inventory_id', string='Line')
    money_ids = fields.One2many('stock.inventory.customer.update.money', 'inventory_id', string='Line')
    therapy_ids = fields.One2many('stock.inventory.customer.update.therapy', 'inventory_id', string='Line')
    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")
    session_id = fields.Many2one('pos.session',string='Session',required=1)
    check = fields.Char('Char')
    transfer_therapy_ids = fields.One2many('transfer.file.therapy', 'inventory_id', string='Transfer')

    @api.model_cr
    def init(self):
        ir_config_obj = self.env['ir.config_parameter']
        if not ir_config_obj.get_param('SP0190'):
            arr = 'BNNMT1_3,BNNMT4_5'
            ir_config_obj.set_param('SP0190', arr)
        if not ir_config_obj.get_param('ONGMTLIPO'):
            arr = 'BLPMT10,BLPMT10_24,BLPMT25_49,BLP50'
            ir_config_obj.set_param('ONGMTLIPO', arr)

    @api.onchange('session_id')
    def _onchange_domain_session(self):
        if not self.session_id:
            param_obj = self.env['ir.config_parameter']
            code = param_obj.get_param('inventory_session')
            if code == False:
                raise ValidationError(
                    _(u"Bạn chưa cấu hình phiên cập nhật tồn. Xin hãy liên hệ với người quản trị."))
            list = code.split(',')
            return {
                'domain': {'session_id': [('id', 'in', list)]}
            }

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.inventory.customer.update') or _('New')
        return super(StockInventoryCustomerUpdate, self).create(vals)

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    @api.multi
    def import_product(self):
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise osv.except_osv("Cảnh báo!",
                                     (
                                         "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 2
            lines = []
            while index < sheet.nrows:
                partner_code = sheet.cell(index, 0).value
                if self.is_number(partner_code):
                    partner_code = '0' + str(int(partner_code))
                partner_obj = self.env['res.partner'].search(['|', '|',  '|', ('x_code', '=', partner_code.strip().upper()),('x_old_code', '=', partner_code.strip().upper()), ('phone', '=', partner_code.strip().upper()), ('mobile', '=', partner_code.strip().upper())], limit=1)
                if partner_obj.id == False:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại khách hàng có mã " + str(
                                         partner_code) + ". Vui lòng kiểm tra lại dòng " + str(
                                         index + 1)))
                else:
                    partner_id = partner_obj.id
                lot_id = False
                product_code = sheet.cell(index, 4).value
                product_obj = self.env['product.product'].search([('default_code', '=', product_code.strip().upper())], limit=1)
                if product_obj.id == False:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại sản phẩm có mã " + str(
                                         product_code) + ". Vui lòng kiểm tra lại dòng " + str(
                                         index + 1)))
                else:
                    product_id = product_obj.id
                    if product_obj.type == 'service':
                        lot_name = sheet.cell(index, 2).value
                        if str(lot_name) == '':
                            raise except_orm('Cảnh báo!',
                                             ("Chưa thêm mã thẻ cho dịch vụ ở dòng " + str(
                                                 index + 1)))
                        if str(lot_name)[0:3] != 'TDT':
                            raise except_orm('Cảnh báo!',
                                             ("Thẻ dịch vụ bạn chọn không phải là thẻ đổ tồn. Vui lòng kiểm tra tại dòng " + str(
                                                 index + 1)))
                        lot_obj = self.env['stock.production.lot'].search([('name', '=', lot_name.strip().upper())],
                                                                          limit=1)
                        if lot_obj.id == False:
                            raise except_orm('Cảnh báo!',
                                             ("Không tồn tại thẻ dịch vụ có mã " + str(
                                                 lot_name) + ". Vui lòng kiểm tra lại dòng " + str(
                                                 index + 1)))
                        else:
                            if lot_obj.x_status != 'actived':
                                raise except_orm('Cảnh báo!',
                                                 ("Thẻ dịch vụ có mã " + str(
                                                     lot_name) + "không ở trạng thái có hiệu lực. Vui lòng kiểm tra lại dòng " + str(
                                                     index + 1)))
                            lot_id = lot_obj.id

                total_qty = sheet.cell(index, 5).value
                qty_use = sheet.cell(index, 6).value
                x_amount = sheet.cell(index, 7).value
                x_payment_amount = sheet.cell(index, 8).value
                note = sheet.cell(index, 9).value
                # if not total_qty or not x_amount or not x_payment_amount or total_qty == '' or x_amount == '' or x_payment_amount == '':
                #     raise except_orm('Cảnh báo!',
                #                      ("Có số lượng chưa cập nhật. Vui lòng kiểm tra lại dòng " + str(index + 1)))
                argvs = {
                    'inventory_id': self.id,
                    'partner_id': partner_id,
                    'product_id': product_id,
                    'lot_id': lot_id,
                    'total_qty': int(total_qty),
                    'qty_hand': int(total_qty) - int(qty_use) if qty_use else int(total_qty),
                    'qty_use': int(qty_use) if qty_use else 0,
                    'x_amount': float(x_amount),
                    'x_payment_amount': float(x_payment_amount),
                    'debt': float(x_amount) - float(x_payment_amount),
                    'note': note,
                }
                lines.append(argvs)
                index = index + 1
            self.product_ids = lines
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    @api.multi
    def import_money(self):
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise osv.except_osv("Cảnh báo!",
                                     (
                                         "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 1
            lines = []
            while index < sheet.nrows:
                partner_code = sheet.cell(index, 1).value.replace(' ', '')
                if self.is_number(partner_code):
                    partner_code = '0' + str(int(partner_code))
                partner_obj = self.env['res.partner'].search(['|', '|', '|', ('x_code', '=', partner_code.strip().upper()),('x_old_code', '=', partner_code.strip().upper()),('phone', '=', partner_code.strip().upper()), ('mobile', '=', partner_code.strip().upper())], limit=1)
                if partner_obj.id == False:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại khách hàng có mã " + str(
                                         partner_code) + ". Vui lòng kiểm tra lại dòng " + str(
                                         index + 1)))
                else:
                    partner_id = partner_obj.id
                x_amount = sheet.cell(index, 3).value
                if not x_amount or x_amount == '':
                    raise except_orm('Cảnh báo!',
                                     ("Có số lượng chưa cập nhật. Vui lòng kiểm tra lại dòng " + str(index + 1)))
                argvs = {
                    'inventory_id': self.id,
                    'partner_id': partner_id,
                    'x_amount': float(x_amount),
                    'note': sheet.cell(index, 4).value
                }
                lines.append(argvs)
                index = index + 1
            self.money_ids = lines
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    @api.multi
    def import_coin(self):
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise osv.except_osv("Cảnh báo!",
                                     (
                                         "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(1)
            index = 2
            lines = []
            while index < sheet.nrows:
                partner_code = sheet.cell(index, 0).value
                if self.is_number(partner_code):
                    partner_code = '0' + str(int(partner_code))
                partner_obj = self.env['res.partner'].search(['|', '|', '|',('x_code', '=', partner_code.strip().upper()),('x_old_code', '=', partner_code.strip().upper()),('phone', '=', partner_code.strip().upper()), ('mobile', '=', partner_code.strip().upper())], limit=1)
                if partner_obj.id == False:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại khách hàng có mã " + str(
                                         partner_code) + ". Vui lòng kiểm tra lại dòng " + str(
                                         index + 1)))
                else:
                    partner_id = partner_obj.id
                product_id = self.env['product.product'].search([('default_code', '=', 'COIN')], limit=1).id
                total_amount_tkc = sheet.cell(index, 6).value
                use_amount_tkc = sheet.cell(index, 7).value
                total_amount_km = sheet.cell(index, 8).value
                use_amount_km = sheet.cell(index, 9).value
                x_amount = sheet.cell(index, 10).value
                x_payment_amount = sheet.cell(index, 11).value
                # if not total_amount_tkc or not x_amount or not x_payment_amount or total_amount_tkc == '' or x_amount == '' or x_payment_amount == '':
                #     raise except_orm('Cảnh báo!',
                #                      ("Có số lượng chưa cập nhật. Vui lòng kiểm tra lại dòng " + str(index + 1)))
                argvs = {
                    'inventory_id': self.id,
                    'partner_id': partner_id,
                    'product_id': product_id,
                    'total_amount_tkc': float(total_amount_tkc),
                    'use_amount_tkc': float(use_amount_tkc),
                    'total_amount_km': float(total_amount_km),
                    'use_amount_km': float(use_amount_km),
                    'x_amount': float(x_amount),
                    'x_payment_amount': float(x_payment_amount),
                    'debt': float(x_amount) - float(x_payment_amount),
                }
                lines.append(argvs)
                index = index + 1
            self.coin_ids = lines
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    @api.multi
    def import_therapy(self):
        try:
            # if not self.categ_id:
            #     raise UserError(_("Bạn phải chọn nhóm sản phẩm/dịch vụ trước khi import"))
            if not self._check_format_excel(self.field_binary_name):
                raise UserError(_("File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 1
            lines = []
            while index < sheet.nrows:
                partner_code = sheet.cell(index, 1).value.replace(' ', '')
                if partner_code == '':
                    raise UserError(_("Cột mã khách hàng trống. Vui lòng kiểm tra lại dòng %s") % str(
                                         index + 1))
                if self.is_number(partner_code):
                    partner_code = '0' + str(int(partner_code))
                partner_obj = self.env['res.partner'].search(
                    ['|', '|', '|', ('x_code', '=', partner_code.strip().upper()),
                     ('x_old_code', '=', partner_code.strip().upper()), ('phone', '=', partner_code.strip().upper()),
                     ('mobile', '=', partner_code.strip().upper())], limit=1)

                if not partner_obj:
                    raise UserError(_("Không tồn tại khách hàng có mã %s. Vui lòng kiểm tra lại dòng %s") % (str(
                                         partner_code), str(index + 1)))
                else:
                    partner_id = partner_obj.id
                product_code = sheet.cell(index, 3).value.replace(' ', '')
                interaction_last_date = sheet.cell(index, 13).value
                out_of_medicine_date = sheet.cell(index, 12).value

                if interaction_last_date != '':
                    if isinstance(interaction_last_date, float) or interaction_last_date.find('-') == -1:
                        raise UserError('Định dạng ngày tương tác cuối cùng %s ở dòng %s chưa đúng định dạng Y-m-d hoặc định dạng ô excel không phải là text' %(interaction_last_date, index+1))
                else:
                    interaction_last_date = False
                if out_of_medicine_date != '':
                    if isinstance(out_of_medicine_date,float) or out_of_medicine_date.find('-') == -1:
                        raise UserError('Định dạng ngày hết thuốc %s ở dòng %s chưa đúng định dạng Y-m-d hoặc định dạng ô excel không phải là text' %(out_of_medicine_date, index+1))
                else:
                    out_of_medicine_date = False
                #kiem tra xem có phải sản phẩm kèm theo không
                # product_id = self.env['product.product'].search([('include_product_id', '=', product_code)])
                # if not product_id:
                product_id = self.env['product.product'].search([('default_code', '=', product_code)])
                if not product_id:
                    raise UserError("Không tồn tại sản phẩm/ dịch vụ có mã %s ở dòng %s" % (sheet.cell(index, 3).value,str(index + 1)))
                categ_id = product_id.categ_id
                # kiểm tra xem sp có nằm trong barem không
                barem_option = self.env['therapy.bundle.barem.option'].search([('product_id', '=', product_id.id)], limit=1)
                if barem_option:
                    categ_id = barem_option.component_id.therapy_bundle_barem_id.categ_id
                therapy_id = False
                if categ_id.x_is_therapy_record or barem_option:
                    if sheet.cell(index, 14).value == '':
                        raise UserError('Thiếu trạng thái hồ sơ trị liệu ở dòng %s' % (index + 1))
                    therapy_id = self.env['therapy.record'].search([('categ_id', '=', categ_id.id), ('partner_id', '=', partner_id)], limit=1)
                    if not therapy_id:
                        therapy_id = self.env['therapy.record'].create({
                            'name': f'Tồn - {partner_obj.name} - {categ_id.name}',
                            'partner_id': partner_id,
                            'categ_id': categ_id.id,
                            'is_inventory': True,
                            'state': sheet.cell(index, 14).value,
                            'interaction_last_date': interaction_last_date,
                            'out_of_medicine_date': out_of_medicine_date,
                            'note': sheet.cell(index, 15).value,
                        })
                    else:
                        if sheet.cell(index, 15).value != '':
                            therapy_id.note = f'{therapy_id.note} - {sheet.cell(index, 15).value}'
                        if not therapy_id.out_of_medicine_date and out_of_medicine_date:
                            therapy_id.out_of_medicine_date = out_of_medicine_date
                        if not therapy_id.is_inventory:
                            therapy_id.is_inventory = True
                # product_id = self.env['product.product'].search([('default_code', '=', sheet.cell(index, 3).value)], limit=1)

                total_amount = sheet.cell(index, 6).value
                amount_inventory = sheet.cell(index, 8).value
                amount_used = sheet.cell(index, 7).value
                total_amount_money = sheet.cell(index, 9).value
                amount_payment = sheet.cell(index, 10).value
                debt = sheet.cell(index, 11).value

                arr_body = sheet.cell(index, 5).value.split(',')
                arr_body_areas = []
                for body in arr_body:
                    if body == '':
                        continue
                    body_area = self.env['body.area'].search([('code', 'like', body.replace(' ', '')), ('type', '=', 'injection')], limit=1)
                    if body_area:
                        arr_body_areas.append(body_area.id)
                if total_amount == '' or amount_inventory == '' or amount_used == '' or total_amount_money == '' or amount_payment == '' or debt == '':
                    raise UserError('Dòng %s đang có một ô bắt buộc nhập bị trống' % str(index + 1))
                argvs = {
                    'inventory_id': self.id,
                    'therapy_id': therapy_id and therapy_id.id or False,
                    'partner_id': partner_id,
                    'product_id': product_id,
                    'total_qty': float(total_amount),
                    'qty_hand': float(amount_inventory),
                    'qty_use': float(amount_used),
                    'total_amount_money': float(total_amount_money),
                    'payment_amount': float(amount_payment),
                    'debt': float(debt),
                    'note': sheet.cell(index, 15).value,
                    'body_area_ids': [(6, 0, arr_body_areas)],
                }
                lines.append(argvs)
                index = index + 1
            self.therapy_ids = lines
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    @api.multi
    def transfer_file(self):
        transfer_file = self.env['transfer.file.therapy'].search([])
        transfer_file.unlink()
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise UserError(_("File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 1
            lines = []
            array_check = ['DV0030', 'DV0031', 'DV0032', 'DV0033', 'DV0034', 'DV0035', 'DV0036', 'DV0037', 'DV0038', 'DV0039']
            while index < sheet.nrows:
                partner_id = sheet.cell(index, 0).value.replace(" ", "")
                product_code_new = sheet.cell(index, 5).value
                product_name_new = sheet.cell(index, 6).value
                check = False
                if partner_id == '':
                    raise UserError(_("Cột mã khách hàng trống. Vui lòng kiểm tra lại dòng %s") % str(
                                         index + 1))
                for record in lines:
                    if record['partner_id'] == partner_id and product_code_new in array_check:
                        array = record['product_code'].split(',')
                        if array[0] in array_check :
                            check = True
                            break
                if check:
                    product_name_old = record['product_name']
                    record['product_name'] = f'{product_name_old},{product_name_new}'
                else:
                    birthday = sheet.cell(index, 4).value
                    if str(birthday).find('/') == -1 and not isinstance(birthday, str):
                        birthday = xlrd.xldate.xldate_as_datetime(birthday, excel.datemode).strftime('%d/%m/%Y')
                    lines.append({
                        'inventory_id': self.id,
                        'partner_id': partner_id,
                        'partner_name': sheet.cell(index, 1).value,
                        'phone': sheet.cell(index, 2).value,
                        'phone_x': sheet.cell(index, 3).value,
                        'birthday': birthday,
                        'product_code': sheet.cell(index, 5).value,
                        'product_name': sheet.cell(index, 6).value,
                        'product_include': sheet.cell(index, 7).value,
                        'total_product': sheet.cell(index, 8).value ,
                        'total_product_used': sheet.cell(index, 9).value ,
                        'massage_actual': sheet.cell(index, 10).value ,
                        'total_amount': sheet.cell(index, 11).value ,
                        'total_payment': sheet.cell(index, 12).value ,
                        'total_paid': sheet.cell(index, 13).value ,
                        'product_note': sheet.cell(index, 14).value,
                        'date_update': sheet.cell(index, 15).value ,
                        })
                index = index + 1
            self.transfer_therapy_ids = lines
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    @api.multi
    def action_print_template(self):
        if self.type == 'therapy':
            return {
                "type": "ir.actions.act_url",
                "url": '/stock_inventory_customer/static/template/import_inventory_customer_therapy.xlsx',
                "target": "_parent",
            }
        if self.type == 'money':
            return {
                "type": "ir.actions.act_url",
                "url": '/stock_inventory_customer/static/template/import_inventory_customer_money.xlsx',
                "target": "_parent",
            }

    @api.multi
    def action_update(self):
        if self.state != 'draft':
            return True
        if self.type == 'product':
            self.import_product()
        elif self.type == 'coin':
            self.import_coin()
        elif self.type == 'therapy':
            self.import_therapy()
        elif self.type == 'transfer':
            self.transfer_file()
        else:
            self.import_money()
        self.state = 'updated'


    @api.multi
    def action_confirm(self):
        if self.state != 'draft':
            return True
        if self.type == 'product' and len(self.product_ids) < 1:
            raise except_orm("Thông báo!", ('Chưa có dịch vụ hoặc sản phẩm đổ tồn. Vui lòng kiểm tra lại trước khi xác nhận'))
        if self.type == 'coin' and len(self.coin_ids) < 1:
            raise except_orm("Thông báo!", ("Chưa có thẻ tiền đổ tồn. Vui lòng kiểm tra lại trước khi xác nhận"))
        if self.type == 'money' and len(self.money_ids) < 1:
            raise except_orm("Thông báo!", ('Chưa có tiền đặt cọc đổ tồn. VUi lòng kiểm tra lại trước khi xác nhận'))
        self.state = 'updated'

    @api.multi
    def action_back(self):
        for line in self.product_ids:
            line.unlink()
        for line in self.coin_ids:
            line.unlink()
        for line in self.money_ids:
            line.unlink()
        for line in self.therapy_ids:
            line.unlink()
        self.state = 'draft'

    @api.multi
    def action_cancel(self):
        self.state = 'cancel'

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Cảnh báo!', ('Không thể xóa bản ghi ở trạng thái khác mới'))
        super(StockInventoryCustomerUpdate, self).unlink()

    @api.multi
    def action_check(self):
        if len(self.product_ids) != 0:
            for line in self.product_ids:
                # check du lieu da ton tai hay chua
                obj_check = self.env['stock.inventory.customer.update.product'].search(
                    [('partner_id', '=', line.partner_id.id), ('product_id', '=', line.product_id.id),('inventory_id.state','=','done')])
                if len(obj_check) != 0:
                    code = ''
                    if line.partner_id.x_code :
                        code = line.partner_id.x_code
                    else:
                        code = line.partner_id.x_old_code
                    sdt = ''
                    if line.partner_id.phone:
                        sdt = line.partner_id.phone
                    else:
                        sdt = line.partner_id.mobile
                    self.check = 'KH có mã '+ str(code)+' hoặc có SĐT '+ str(sdt)
                    view = self.env.ref('stock_inventory_customer.import_stock_inventory_customer_form_check')
                    return {
                        'name': _('Update'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'stock.inventory.customer.update',
                        'views': [(view.id, 'form')],
                        'view_id': view.id,
                        'target': 'new',
                        'res_id': self.id,
                        'context': self.env.context,
                    }
        if len(self.coin_ids) != 0:
            for line in self.coin_ids:
                # check du lieu da ton tai hay chua
                obj_check = self.env['stock.inventory.customer.update.coin'].search(
                    [('partner_id', '=', line.partner_id.id), ('product_id', '=', line.product_id.id),('inventory_id.state','=','done')])
                if len(obj_check) != 0:
                    code = ''
                    if line.partner_id.x_code:
                        code = line.partner_id.x_code
                    else:
                        code = line.partner_id.x_old_code
                    sdt = ''
                    if line.partner_id.phone:
                        sdt = line.partner_id.phone
                    else:
                        sdt = line.partner_id.mobile
                    self.check = 'KH có mã ' + str(code) + ' hoặc có SĐT ' + str(sdt)
                    view = self.env.ref('stock_inventory_customer.import_stock_inventory_customer_form_check')
                    return {
                        'name': _('Update'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'stock.inventory.customer.update',
                        'views': [(view.id, 'form')],
                        'view_id': view.id,
                        'target': 'new',
                        'res_id': self.id,
                        'context': self.env.context,
                    }
        if len(self.money_ids) != 0:
            for line in self.money_ids:
                # check du lieu da ton tai hay chua
                obj_check = self.env['stock.inventory.customer.update.money'].search(
                    [('partner_id', '=', line.partner_id.id), ('inventory_id.state', '=', 'done')])
                if len(obj_check) != 0:
                    code = ''
                    if line.partner_id.x_code:
                        code = line.partner_id.x_code
                    else:
                        code = line.partner_id.x_old_code
                    sdt = ''
                    if line.partner_id.phone:
                        sdt = line.partner_id.phone
                    else:
                        sdt = line.partner_id.mobile
                    self.check = 'KH có mã ' + str(code) + ' hoặc có SĐT ' + str(sdt)
                    view = self.env.ref('stock_inventory_customer.import_stock_inventory_customer_form_check')
                    return {
                        'name': _('Update'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'stock.inventory.customer.update',
                        'views': [(view.id, 'form')],
                        'view_id': view.id,
                        'target': 'new',
                        'res_id': self.id,
                        'context': self.env.context,
                    }
        if len(self.therapy_ids) !=0:
            for line in self.money_ids:
                obj_check = self.env['stock.inventory.customer.update.therapy'].search(
                    [('partner_id', '=', line.partner_id.id), ('inventory_id.state', '=', 'done')])
                if len(obj_check) != 0:
                    code = ''
                    if line.partner_id.x_code:
                        code = line.partner_id.x_code
                    else:
                        code = line.partner_id.x_old_code
                    sdt = ''
                    if line.partner_id.phone:
                        sdt = line.partner_id.phone
                    else:
                        sdt = line.partner_id.mobile
                    self.check = 'KH có mã ' + str(code) + ' hoặc có SĐT ' + str(sdt)
                    view = self.env.ref('stock_inventory_customer.import_stock_inventory_customer_form_check')
                    return {
                        'name': _('Update'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'stock.inventory.customer.update',
                        'views': [(view.id, 'form')],
                        'view_id': view.id,
                        'target': 'new',
                        'res_id': self.id,
                        'context': self.env.context,
                    }

        self.action_done()
        return True

    @api.multi
    def action_done(self):
        if self.state != 'updated':
            return True
        session_id = self.session_id
        if session_id.id == False:
            raise except_orm('Cảnh báo!', ("Chưa có phiên được mở ở điểm bán hàng của bạn!"))
        self._product_pos(session_id)
        self._coin_pos(session_id)
        self._money_pos(session_id)
        self._therapy_pos(session_id)
        self.state = 'done'
        return True

    def _product_pos(self, session_id):
        if len(self.product_ids) != 0:
            for line in self.product_ids:
                if line.product_id.type == 'service':
                    pos_order_line = self.env['pos.order.line'].search([('lot_name','=',line.lot_id.name)])
                    if pos_order_line.id == False:
                        if line.lot_id.x_status != 'actived':
                            raise except_orm('Cảnh báo!',
                                             ("Thẻ có mã " + str(
                                                 line.lot_id.name) + " đang không ở trạng thái đã kích hoạt. Vui lòng thay thẻ mới!"))
                        # tao pos_order
                        PosOrder = self.env['pos.order']
                        argv = {
                            'session_id': session_id.id,
                            'partner_id': line.partner_id.id,
                            'state': 'done',
                            'note': 'Update inventory customer.'
                        }
                        order_id = PosOrder.with_context(inventory_update=True).create(argv)
                        if round(line.x_amount / line.total_qty) - (line.x_amount / line.total_qty) == 0:
                            vals = {
                                'product_id': line.product_id.id,
                                'qty': line.total_qty,
                                'price_unit': line.x_amount / line.total_qty,
                                'order_id': order_id.id,
                            }
                            self.env['pos.order.line'].create(vals)
                        elif round(line.x_amount / line.total_qty) - (line.x_amount / line.total_qty) < 0.5:
                            vals = {
                                'product_id': line.product_id.id,
                                'qty': line.total_qty,
                                'price_unit': round(line.x_amount / line.total_qty) +1,
                                'order_id': order_id.id,
                                'x_discount': -(line.x_amount - ((round(line.x_amount / line.total_qty)+1)*line.total_qty))
                            }
                            self.env['pos.order.line'].create(vals)
                        else:
                            vals = {
                                'product_id': line.product_id.id,
                                'qty': line.total_qty,
                                'price_unit': round(line.x_amount / line.total_qty),
                                'order_id': order_id.id,
                                'x_discount': -(line.x_amount - (
                                            (round(line.x_amount / line.total_qty)) * line.total_qty))
                            }
                            self.env['pos.order.line'].create(vals)
                        vals = {
                            'product_id': line.lot_id.product_id.id,
                            'lot_name': line.lot_id.name,
                            'qty': 1,
                            'price_unit': 0,
                            'order_id': order_id.id,
                        }
                        self.env['pos.order.line'].create(vals)
                    else:
                        if round(line.x_amount / line.total_qty) - (line.x_amount / line.total_qty) == 0:
                            vals = {
                                'product_id': line.product_id.id,
                                'qty': line.total_qty,
                                'price_unit': line.x_amount / line.total_qty,
                                'order_id': pos_order_line.order_id.id,
                            }
                            self.env['pos.order.line'].create(vals)
                        elif round(line.x_amount / line.total_qty) - (line.x_amount / line.total_qty) < 0.5:
                            vals = {
                                'product_id': line.product_id.id,
                                'qty': line.total_qty,
                                'price_unit': round(line.x_amount / line.total_qty) +1,
                                'order_id': pos_order_line.order_id.id,
                                'x_discount': -(line.x_amount - ((round(line.x_amount / line.total_qty)+1)*line.total_qty))
                            }
                            self.env['pos.order.line'].create(vals)
                        else:
                            vals = {
                                'product_id': line.product_id.id,
                                'qty': line.total_qty,
                                'price_unit': round(line.x_amount / line.total_qty),
                                'order_id': pos_order_line.order_id.id,
                                'x_discount': -(line.x_amount - (
                                            (round(line.x_amount / line.total_qty)) * line.total_qty))
                            }
                            self.env['pos.order.line'].create(vals)
                        order_id = pos_order_line.order_id
                    # order_id.x_lot_number = line.lot_id.name
                    # order_id.action_search_lot_number()
                    # cap nhat chi tiet the
                    argvs = {
                        'lot_id': line.lot_id.id,
                        'product_id': line.product_id.id,
                        'total_qty': line.total_qty,
                        'qty_hand': line.qty_hand,
                        'qty_use': line.qty_use,
                        'price_unit': round(line.x_amount / line.total_qty),
                        'remain_amount': line.qty_hand * round(line.x_amount / line.total_qty),
                        'amount_total': line.x_amount,
                        'note': line.note,
                    }
                    self.env['izi.service.card.detail'].create(argvs)
                    line.lot_id.x_payment_amount = line.x_payment_amount
                    if line.total_qty == line.qty_use:
                        line.lot_id.x_status = 'used'
                    else:
                        line.lot_id.x_status = 'using'
                    line.lot_id.x_customer_id = line.partner_id.id
                    if line.lot_id.x_release_id.expired_type == '1':
                        date = datetime.strptime(self.date, "%Y-%m-%d %H:%M:%S") + relativedelta(
                            months=line.lot_id.x_release_id.validity)
                        line.lot_id.life_date = date.replace(minute=0, hour=0, second=0)
                    line.lot_id.x_amount = line.x_amount
                    line.lot_id.x_order_id = order_id.id
                    # tạo account.bank.statement.line
                    journal_id = False
                    # for jo in session_id.config_id.journal_loyal_ids:
                    #     journal_id = jo
                    #     if journal_id.id != False:
                    #         break
                    statement_id = False
                    for statement in session_id.statement_ids:
                        if statement.id == statement_id:
                            break
                        elif statement.journal_id.id in session_id.config_id.journal_loyal_ids.ids:
                            statement_id = statement.id
                            journal_id = statement.journal_id
                            break
                    company_cxt = dict(self.env.context, force_company=journal_id.company_id.id)
                    account_def = self.env['ir.property'].with_context(company_cxt).get(
                        'property_account_receivable_id',
                        'res.partner')
                    account_id = (line.partner_id.property_account_receivable_id.id) or (
                            account_def and account_def.id) or False
                    if line.x_payment_amount > 0:
                        argvs = {
                            'ref': session_id.name,
                            'name': 'update',
                            'partner_id': line.partner_id.id,
                            'amount': line.x_payment_amount,
                            'account_id': account_id,
                            'statement_id': statement_id,
                            'journal_id': journal_id.id,
                            'date': self.date,
                            'pos_statement_id': order_id.id
                        }
                        self.env['account.bank.statement.line'].create(argvs)
                    if (line.x_amount - line.x_payment_amount) > 0:
                        statement_id = False
                        for statement in session_id.statement_ids:
                            if statement.id == statement_id:
                                break
                            elif statement.journal_id.id == session_id.config_id.journal_debt_id.id:
                                statement_id = statement.id
                                break
                        argvs_debt = {
                            'ref': session_id.name,
                            'name': 'update',
                            'partner_id': line.partner_id.id,
                            'amount': line.x_amount - line.x_payment_amount,
                            'account_id': account_id,
                            'statement_id': statement_id,
                            'journal_id': session_id.config_id.journal_debt_id.id,
                            'date': self.date,
                            'pos_statement_id': order_id.id,
                        }
                        self.env['account.bank.statement.line'].create(argvs_debt)
                    # order_id.action_order_complete()
                    line.partner_id.x_balance = line.partner_id.x_balance + 2*line.x_payment_amount - line.x_amount - line.qty_use * line.x_amount / line.total_qty
                else:
                    PosOrder = self.env['pos.order']
                    argv = {
                        'session_id': session_id.id,
                        'partner_id': line.partner_id.id,
                        'state': 'done',
                        'note': 'Update inventory customer.'
                    }
                    order_id = PosOrder.with_context(inventory_update=True).create(argv)
                    if round(line.x_amount / line.total_qty) - (line.x_amount / line.total_qty) == 0:
                        vals = {
                            'product_id': line.product_id.id,
                            'qty': line.total_qty,
                            'price_unit': line.x_amount / line.total_qty,
                            'order_id': order_id.id,
                        }
                        self.env['pos.order.line'].create(vals)
                    elif round(line.x_amount / line.total_qty) - (line.x_amount / line.total_qty) < 0.5:
                        vals = {
                            'product_id': line.product_id.id,
                            'qty': line.total_qty,
                            'price_unit': round(line.x_amount / line.total_qty) + 1,
                            'order_id': order_id.id,
                            'x_discount': -(line.x_amount - ((round(line.x_amount / line.total_qty) + 1) * line.total_qty))
                        }
                        self.env['pos.order.line'].create(vals)
                    else:
                        vals = {
                            'product_id': line.product_id.id,
                            'qty': line.total_qty,
                            'price_unit': round(line.x_amount / line.total_qty),
                            'order_id': order_id.id,
                            'x_discount': -(line.x_amount - (
                                    (round(line.x_amount / line.total_qty)) * line.total_qty))
                        }
                        self.env['pos.order.line'].create(vals)
                    # vals = {
                    #     'product_id': line.product_id.id,
                    #     'qty': line.total_qty,
                    #     'price_unit': line.x_amount / line.total_qty,
                    #     'order_id': order_id.id,
                    # }
                    # self.env['pos.order.line'].create(vals)
                    journal_id = False
                    # for jo in session_id.config_id.journal_loyal_ids:
                    #     journal_id = jo
                    #     if journal_id.id != False:
                    #         break
                    statement_id = False
                    for statement in session_id.statement_ids:
                        if statement.id == statement_id:
                            break
                        elif statement.journal_id.id in session_id.config_id.journal_loyal_ids.ids:
                            statement_id = statement.id
                            journal_id = statement.journal_id
                            break
                    company_cxt = dict(self.env.context, force_company=journal_id.company_id.id)
                    account_def = self.env['ir.property'].with_context(company_cxt).get(
                        'property_account_receivable_id',
                        'res.partner')
                    account_id = (line.partner_id.property_account_receivable_id.id) or (
                            account_def and account_def.id) or False
                    if line.x_payment_amount > 0:
                        argvs = {
                            'ref': session_id.name,
                            'name': 'update',
                            'partner_id': line.partner_id.id,
                            'amount': line.x_payment_amount,
                            'account_id': account_id,
                            'statement_id': statement_id,
                            'journal_id': journal_id.id,
                            'date': self.date,
                            'pos_statement_id': order_id.id
                        }
                        self.env['account.bank.statement.line'].create(argvs)
                    if (line.x_amount - line.x_payment_amount) > 0:
                        statement_id = False
                        for statement in session_id.statement_ids:
                            if statement.id == statement_id:
                                break
                            elif statement.journal_id.id == session_id.config_id.journal_debt_id.id:
                                statement_id = statement.id
                                break
                        argvs_debt = {
                            'ref': session_id.name,
                            'name': 'update',
                            'partner_id': line.partner_id.id,
                            'amount': line.x_amount - line.x_payment_amount,
                            'account_id': account_id,
                            'statement_id': statement_id,
                            'journal_id': session_id.config_id.journal_debt_id.id,
                            'date': self.date,
                            'pos_statement_id': order_id.id,
                        }
                        self.env['account.bank.statement.line'].create(argvs_debt)
                    # tao don quan ly no hang
                    Debit = self.env['pos.debit.good']
                    DebitLine = self.env['pos.debit.good.line']
                    db = Debit.search([('partner_id', '=', line.partner_id.id)], limit=1)
                    if db.id != False:
                        debit_id = db
                    else:
                        debit_vals = {
                            'partner_id': line.partner_id.id,
                            'code': line.partner_id.x_code,
                            'old_code': line.partner_id.x_old_code,
                            'phone': line.partner_id.phone,
                            'mobile': line.partner_id.mobile,
                            'state': 'debit',
                        }
                        debit_id = Debit.create(debit_vals)
                    debit_vals_line = {
                        'order_id': order_id.id,
                        'product_id': line.product_id.id,
                        'qty': line.qty_hand,
                        'qty_depot': 0,
                        'qty_debit': line.qty_hand,
                        'date': self.date,
                        'debit_id': debit_id.id,
                        'note': 'Update inventory',
                    }
                    DebitLine.create(debit_vals_line)
                    line.partner_id.x_balance = line.partner_id.x_balance + 2*line.x_payment_amount - line.x_amount
                line.order_id = order_id.id
            for line in self.product_ids:
                if line.order_id.invoice_id.id == False:
                    line.order_id.create_invoice()
        return True

    def _coin_pos(self, session_id):
        if len(self.coin_ids) != 0:
            for line in self.coin_ids:
                PosOrder = self.env['pos.order']
                argv = {
                    'session_id': session_id.id,
                    'partner_id': line.partner_id.id,
                    'state': 'done',
                    'note': 'Update inventory customer.'
                }
                order_id = PosOrder.with_context(inventory_update=True).create(argv)
                # tai khoan chinh
                vals1 = {
                    'product_id': line.product_id.id,
                    'qty': line.total_amount_tkc / line.product_id.product_tmpl_id.list_price,
                    'price_unit': line.product_id.product_tmpl_id.list_price,
                    'order_id': order_id.id,
                }
                coin1 = {
                    'partner_id': line.partner_id.id,
                    'money': line.total_amount_tkc,
                    'debt_amount': line.x_amount - line.x_payment_amount,
                    'order_id': order_id.id,
                    'money_used': line.use_amount_tkc,
                    'typex': '1'
                }
                self.env['pos.order.line'].create(vals1)
                tkc_vitual_money_id =  self.env['pos.virtual.money'].create(coin1)
                # tai khoan km
                vals2 = {
                    'product_id': line.product_id.id,
                    'qty': line.total_amount_km / line.product_id.product_tmpl_id.list_price,
                    'price_unit': line.product_id.product_tmpl_id.list_price,
                    'discount': 100,
                    'order_id': order_id.id,
                }
                debt = 0
                if line.debt > 0:
                    debt += line.total_amount_km
                else:
                    debt += 0
                coin2 = {
                    'partner_id': line.partner_id.id,
                    'money': line.total_amount_km,
                    'debt_amount': debt,
                    'order_id': order_id.id,
                    'money_used': line.use_amount_km,
                    'typex': '2',
                }
                self.env['pos.order.line'].create(vals2)
                tkkm_vitual_money_id = self.env['pos.virtual.money'].create(coin2)
                tkc_vitual_money_id.update({'sub_amount_id':tkkm_vitual_money_id.id})
                # tạo account.bank.statement.line
                journal_id = False
                # for jo in session_id.config_id.journal_loyal_ids:
                #     journal_id = jo
                #     if journal_id.id != False:
                #         break
                statement_id = False
                for statement in session_id.statement_ids:
                    if statement.id == statement_id:
                        break
                    elif statement.journal_id.id in session_id.config_id.journal_loyal_ids.ids:
                        statement_id = statement.id
                        journal_id = statement.journal_id
                        break
                company_cxt = dict(self.env.context, force_company=journal_id.company_id.id)
                account_def = self.env['ir.property'].with_context(company_cxt).get('property_account_receivable_id',
                                                                                    'res.partner')
                account_id = (line.partner_id.property_account_receivable_id.id) or (
                        account_def and account_def.id) or False
                if line.x_payment_amount >0 :
                    argvs = {
                        'ref': session_id.name,
                        'name': 'update',
                        'partner_id': line.partner_id.id,
                        'amount': line.x_payment_amount,
                        'account_id': account_id,
                        'statement_id': statement_id,
                        'journal_id': journal_id.id,
                        'date': self.date,
                        'pos_statement_id': order_id.id
                    }
                    self.env['account.bank.statement.line'].create(argvs)
                if (line.x_amount - line.x_payment_amount) > 0:
                    statement_id = False
                    for statement in session_id.statement_ids:
                        if statement.id == statement_id:
                            break
                        elif statement.journal_id.id == session_id.config_id.journal_debt_id.id:
                            statement_id = statement.id
                            break
                    argvs_debt = {
                        'ref': session_id.name,
                        'name': 'update',
                        'partner_id': line.partner_id.id,
                        'amount': line.x_amount - line.x_payment_amount,
                        'account_id': account_id,
                        'statement_id': statement_id,
                        'journal_id': session_id.config_id.journal_debt_id.id,
                        'date': self.date,
                        'pos_statement_id': order_id.id,
                    }
                    self.env['account.bank.statement.line'].create(argvs_debt)
                line.partner_id.x_balance = line.partner_id.x_balance + 2 * line.x_payment_amount - line.x_amount - line.use_amount_tkc - line.use_amount_km
                line.order_id = order_id.id
                line.order_id.create_invoice()
        return True

    def _money_pos(self, session_id):
        if len(self.money_ids) != 0:
            for line in self.money_ids:
                # tao master
                Master = self.env['pos.customer.deposit']
                deposit_id = Master.search([('partner_id', '=', line.partner_id.id)], limit=1)
                if deposit_id.id == False:
                    if session_id.config_id.journal_deposit_id.id == False:
                        raise except_orm('Cảnh báo!', (
                            "Điểm bán hàng của bạn chưa cấu hình phương thức ghi nhận đặt cọc"))
                    vals = {
                        'name': line.partner_id.name,
                        'partner_id': line.partner_id.id,
                        'journal_id': session_id.config_id.journal_deposit_id.id,
                    }
                    master_id = Master.create(vals)
                    deposit_obj = master_id
                else:
                    deposit_obj = deposit_id
                # tao line
                journal_id = False
                for jo in session_id.config_id.journal_deposit_ids:
                    journal_id = jo
                    if journal_id.id != False:
                        break
                vals_line = {
                    'session_id':session_id.id,
                    'x_type':'deposit',
                    'type': 'deposit',
                    'partner_id': line.partner_id.id,
                    'journal_id': journal_id.id,
                    'amount': line.x_amount,
                    'deposit_id': deposit_obj.id,
                    'state': 'done',
                    'note': line.note
                }
                self.env['pos.customer.deposit.line'].with_context(inventory_update=True).create(vals_line)
                line.partner_id.x_balance = line.partner_id.x_balance + line.x_amount
                # tao move
                move_lines = []
                credit_move_vals = {
                    'name': self.name,
                    'account_id': deposit_obj.journal_id.default_credit_account_id.id,
                    'credit': line.x_amount,
                    'debit': 0.0,
                    'partner_id': line.partner_id.id,
                }
                debit_move_vals = {
                    'name': self.name,
                    'account_id': journal_id.default_debit_account_id.id,
                    'credit': 0.0,
                    'debit': line.x_amount,
                    'partner_id': line.partner_id.id,
                }
                move_lines.append((0, 0, debit_move_vals))
                move_lines.append((0, 0, credit_move_vals))
                vals_account = {
                    'date': fields.Datetime.now(),
                    'ref': self.name,
                    'journal_id': journal_id.id,
                    'line_ids': move_lines
                }
                move_id = self.env['account.move'].create(vals_account)
                move_id.post()
                deposit_obj.account_move_ids = [(4, move_id.id)]
                # tao account_bank_statement_line
                statement_id = False
                for statement in session_id.statement_ids:
                    if statement.id == statement_id:
                        journal_id = statement.journal_id.id
                        break
                    elif statement.journal_id.id == journal_id.id:
                        statement_id = statement.id
                        break
                company_cxt = dict(self.env.context, force_company=journal_id.company_id.id)
                account_def = self.env['ir.property'].with_context(company_cxt).get('property_account_receivable_id',
                                                                                    'res.partner')
                account_id = (line.partner_id.property_account_receivable_id.id) or (
                        account_def and account_def.id) or False
                amount = line.x_amount
                argvs = {
                    'ref': session_id.name,
                    'name': 'Deposit',
                    'partner_id': line.partner_id.id,
                    'amount': amount,
                    'account_id': account_id,
                    'statement_id': statement_id,
                    'journal_id': journal_id.id,
                    'date': self.date,
                }
                self.env['account.bank.statement.line'].create(argvs)
        return True

    def _therapy_pos(self, session_id):
        therapies_obj = self.env['therapy.record'].search([])
        arr_partner = []
        for therapy_id in self.therapy_ids:
            arr_partner.append(therapy_id.partner_id.id)
        for partner in set(arr_partner):
            arr_excel = []
            arr_therapy_id = []
            order_id = False
            #lấy ra các dòng trong file excel cùng 1 partner
            for arr_therapy in self.therapy_ids.filtered(lambda therapy: therapy.partner_id.id == partner):
                arr_excel.append({
                    'therapy_record': arr_therapy.therapy_id.id,
                    'product_id': arr_therapy.product_id.id,
                    'qty_hand': arr_therapy.qty_hand,
                    'qty_used': arr_therapy.qty_use,
                    'qty_total': arr_therapy.total_qty,
                    'total_amount_money': arr_therapy.total_amount_money,
                    'payment_amount': arr_therapy.payment_amount,
                    'debit': arr_therapy.debt,
                    'note': arr_therapy.note,
                    'body_area_ids': arr_therapy.body_area_ids.ids,
                })
                arr_therapy_id.append(arr_therapy.therapy_id)
            if len(arr_excel) > 0:
                order_id = self._create_pos_order(arr_excel, partner)
                self._create_therapy_bundle_product(arr_excel, set(arr_therapy_id), order_id)
                self.create_mail_activity_medicine(set(arr_therapy_id))

    def create_mail_activity_medicine(self, arr_therapy_id):
        for therapy_obj in arr_therapy_id:
            if therapy_obj.out_of_medicine_date:
                out_of_date = datetime.strptime(therapy_obj.out_of_medicine_date, '%Y-%m-%d')
                # todo tạo lịch nhắc thuốc sau khi xuất đơn kho
                arr = self.env['ir.config_parameter'].sudo().get_param('Remind.Medicine')
                arr_config = json.loads(arr.replace("'", "\""))
                reminds_created = self.env['activity.history'].search(
                    [('therapy_record_id', '=', therapy_obj.id), ('state', 'not in', ['interacted', 'cancel']),
                     ('type', '=', 'out_of_medicine')], limit=1)
                date_deadline = out_of_date - timedelta(days=arr_config['date_deadline'])
                if not reminds_created:
                    remind = self.env['activity.history'].create({
                        'partner_id': therapy_obj.partner_id.id,
                        'therapy_record_id': therapy_obj.id,
                        'mail_activity_type_id': arr_config['activity_type_id'],
                        'type': 'out_of_medicine',
                        'object': 'consultant',
                        'user_id': therapy_obj.partner_id.user_id.id,
                        'date_deadline': date_deadline,
                    })
                    remind.action_assign()
                else:
                    reminds_created.date_deadline = date_deadline


    #tạo gọi liệu trình
    def _create_therapy_bundle(self,arr_excel, therapy_id, order_id):
        products_order = []
        amount_total = 0
        product_product_obj = self.env['product.product']
        therapy = self.env['therapy.record'].search([('id', '=', therapy_id)], limit=1)
        for row in arr_excel:
            product = product_product_obj.search([('id', '=', int(row['product_id']))], limit=1)
            # thêm các dịch vụ bắn tương ứng với những sp kèm dịch vụ bắn
            str_service_injection = self.env['ir.config_parameter'].sudo().get_param(product.default_code)
            if str_service_injection:
                arr_service_injection= str_service_injection.split(',')
                for service_injection in arr_service_injection:
                    service = product_product_obj.search([('default_code', '=', service_injection)])
                    if service:
                        products_order.append({
                            'product_id': service.id,
                            'uom_id': service.uom_id.id,
                            'qty': -1,
                            'body_area_ids': False,
                        })
            amount_total += row['total_amount_money']
            products_order.append({
                'product_id': product.id,
                'uom_id': product.uom_id.id,
                'qty': row['qty_total'],
                'body_area_ids': row['body_area_ids'],
            })
        therapy_bundle_line_ids = []
        for product_order in products_order:
            therapy_bundle_line_ids.append((0, 0, product_order))
            if product_order.get('body_area_ids', False):
                print(product_order['body_area_ids'])
                body_area_ids = product_order['body_area_ids']
                product_order['body_area_ids'] = []
                product_order['body_area_ids'].append((6, 0, body_area_ids))
                print(product_order['body_area_ids'])
        offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
        hours = offset / 60 / 60 * -1
        date = datetime.now().date() + timedelta(hours=hours)
        therapy_bundle = {
            'amount_total': amount_total,
            'therapy_record_id': therapy.id,
            'therapy_bundle_line_ids': therapy_bundle_line_ids,
            'order_id': order_id,
            'name': 'GLT_'+ str(therapy.partner_id.x_code) + '_' + str(date),
        }
        self.env['therapy.bundle'].create(therapy_bundle)

    #đổ tồn hstl
    def _create_therapy_bundle_product(self, arr_excel, arr_therapy_id, order_id):
        for therapy_id in arr_therapy_id:
            product_product_obj = self.env['product.product']
            for row in arr_excel:
                if row['therapy_record'] == therapy_id.id:
                    product_id = product_product_obj.search([('id', '=', int(row['product_id']))], limit=1)
                    if len(order_id.lines.filtered(lambda row:row.product_id.id == product_id.id)) == 0:
                        order_line_id = False
                        price_unit = amount_paid = actual_debt = price_subtotal_incl = 0
                    else:
                        order_line_id = row['order_line_id']
                        amount_paid = actual_debt = 0
                        price_unit = int(row['total_amount_money'] / row['qty_total'])
                        price_subtotal_incl = row['total_amount_money']
                    body_area_ids = False
                    if len(row['body_area_ids']) > 0:
                        body_area_ids = self.env['body.area'].search([('id', 'in', row['body_area_ids'])])
                    self.env['therapy.record.product'].create({
                        'therapy_record_id': therapy_id.id,
                        'product_id': product_id.id,
                        'uom_id': product_id.uom_id.id,
                        'qty_used': row['qty_used'],
                        'qty_max': row['qty_total'],
                        'order_id': order_id.id,
                        'order_line_id': order_line_id,
                        'price_unit': price_unit,
                        'body_area_ids': [(6, 0, body_area_ids.ids)] if body_area_ids else False,  # [(4, k) for k in row['body_area_ids']],
                        'price_subtotal_incl': price_subtotal_incl,

                    })
            #thêm các dịch vụ bắn tương ứng với những sp kèm dịch vụ bắn
            # str_service_injection = self.env['ir.config_parameter'].sudo().get_param(product.default_code)
            # if str_service_injection:
            #     arr_service_injection = str_service_injection.split(',')
            #     for service_injection in arr_service_injection:
            #         service = product_product_obj.search([('default_code', '=', service_injection)])
            #         if service:
            #             products_order.append({
            #                 'product_id': service.id,
            #                 'qty': 0,
            #                 'qty_max': -1,
            #                 'body_area_ids': False,
            #             })
            # thêm sản phẩm/ dịch vụ bình thường của file excel
            # products_order.append({
            #     'product_id': row['product_id'],
            #     'qty': row['qty_used'],
            #     'qty_max': row['qty_total'],
            #     'body_area_ids': row['body_area_ids'],
            # })
        # for product_order in products_order:
        #     check = True
        #     if product_order['qty_max'] == 0:
        #         continue
        #     if therapy.therapy_record_product_ids:
        #         for therapy_record_product in therapy.therapy_record_product_ids:
        #             if product_order['product_id'] == therapy_record_product.product_id.id:
        #                 check = False
        #                 therapy_record_product.qty_used += product_order['qty']
        #                 if product_order['qty'] != -1:
        #                     therapy_record_product.qty_max += product_order['qty_max']
        #                 break
        #     product = self.env['product.template'].search([('id', '=', int(product_order['product_id']))])
        #     if check:
        #         self.env['therapy.record.product'].create({
        #             'therapy_record_id': therapy_id,
        #             'product_id': product.id,
        #             'uom_id': product.uom_id.id,
        #             'qty_used': product_order['qty'],
        #             'qty_max': product_order['qty_max'],
        #         })

    #tạo đơn hàng
    def _create_pos_order(self, arr_excel, partner_id):
        PosOrder = self.env['pos.order']
        BankStatement = self.env['account.bank.statement']
        ProductProduct = self.env['product.product']
        partner = self.env['res.partner'].search([('id', '=', partner_id)])
        argv = {
            'session_id': self.session_id.id,
            'partner_id': partner.id,
            'state': 'done',
            'note': 'Update inventory customer.',
            'x_is_create_therapy_record': True,
        }
        order_id = PosOrder.with_context(inventory_update=True).create(argv)
        amount_total = 0
        for line in arr_excel:
            product_id = ProductProduct.search([('id', '=', line['product_id'])], limit=1)
            # tạo dữ liệu cho sản phẩm bổ trợ trên đơn hàng
            barem_option = self.env['therapy.bundle.barem.option'].search([('product_id', '=', product_id.id)], limit=1)
            if barem_option:
                vals = {
                    'product_id': line['product_id'],
                    'component_id': barem_option.component_id.id,
                    'categ_id': barem_option.component_id.therapy_bundle_barem_id.categ_id.id,
                    'barem_id': barem_option.component_id.therapy_bundle_barem_id.id,
                    'qty': line['qty_total'],
                    'qty_max': line['qty_total'],
                    'uom_id': product_id.uom_id.id,
                    'pos_order_id': order_id.id,
                }
                self.env['pos.order.complement'].create(vals)
            # tạo dữ liệu cho chi tiết đơn hàng
            else:
                vals = {
                    'product_id': line['product_id'],
                    'qty': line['qty_total'],
                    'price_unit': line['total_amount_money'] / line['qty_total'] if line['qty_total'] != 0 else 0,
                    'order_id': order_id.id,
                    'x_body_area_ids': [(6, 0, line['body_area_ids'])],
                    'price_subtotal_incl': line['total_amount_money'],
                }
                order_line_id = self.env['pos.order.line'].create(vals)
                line['order_line_id'] = order_line_id.id
                amount_total += line['total_amount_money']
                # Tạo dư liệu cho tab thanh toán
                journal_id = False
                statement_id = False
                # for statement in self.session_id.statement_ids:
                #     if statement.id == statement_id:
                #         break
                #     elif statement.journal_id.id in self.session_id.config_id.journal_loyal_ids.ids:
                #         statement_id = statement.id
                #         journal_id = statement.journal_id
                #         break
                #gán trực tiếp hình thức thanh toán tiền mặt vào thanh toán đơn hàng
                journal_id = self.env['account.journal'].search([('code', '=', 'CSH1')])
                if not journal_id:
                    raise UserError('Bạn chưa cấu hình phương thức thanh toán Tiền mặt')
                statement = self.env['account.bank.statement'].search([('journal_id', '=', journal_id.id), ('pos_session_id', '=', self.session_id.id)])
                if not statement:
                    statement = BankStatement.create({'journal_id': journal_id.id, 'user_id': self.env.uid, 'name': 'pos session import'})
                company_cxt = dict(self.env.context, force_company=journal_id.company_id.id)
                account_def = self.env['ir.property'].with_context(company_cxt).get(
                    'property_account_receivable_id',
                    'res.partner')
                account_id = (partner.property_account_receivable_id.id) or (
                        account_def and account_def.id) or False
                if line['payment_amount'] > 0:
                    argvs = {
                        'ref': self.session_id.name,
                        'name': 'update',
                        'partner_id': partner.id,
                        'amount': line['payment_amount'],
                        'account_id': account_id,
                        'statement_id': statement.id,
                        'journal_id': journal_id.id,
                        'date': self.date,
                        'pos_statement_id': order_id.id
                    }
                    self.env['account.bank.statement.line'].create(argvs)
                if line['debit'] > 0:
                    statement_id = False
                    for statement in self.session_id.statement_ids:
                        if statement.id == statement_id:
                            break
                        elif statement.journal_id.id == self.session_id.config_id.journal_debt_id.id:
                            statement_id = statement.id
                            break
                    if not statement_id:
                        statement_id = BankStatement.create(
                            {'journal_id': self.session_id.config_id.journal_debt_id.id, 'user_id': self.env.uid, 'name': 'pos session import'}).id
                    argvs_debt = {
                        'ref': self.session_id.name,
                        'name': 'update',
                        'partner_id': partner.id,
                        'amount': line['debit'],
                        'account_id': account_id,
                        'statement_id': statement_id,
                        'journal_id': self.session_id.config_id.journal_debt_id.id,
                        'date': self.date,
                        'pos_statement_id': order_id.id,
                    }
                    self.env['account.bank.statement.line'].create(argvs_debt)
        if order_id.x_pos_order_complement_ids:
            order_id.x_is_create_therapy_record = True
        if order_id.invoice_id.id == False and order_id.lines:
            order_id.create_invoice()
        # kiểm tra chi tiết đơn hàng có dv cần gắn thẻ dịch vụ k
        if len(order_id.lines.filtered(lambda line: not line.product_id.categ_id.x_is_therapy_record and line.product_id.type == 'service')) > 0:
            # tạo thẻ dịch vụ gắn với dịch vụ
            order_id.with_context(inventory_therapy=True)._add_service_to_service_card()
            # cập nhật thẻ dịch vụ
            order_id._update_service_card_import(arr_excel)


        order_id.update({
            'amount_total': amount_total,
        })
        #phân bổ thanh toán
        order_id.pos_payment_allocation(arr_excel)
        pos_payment_ids = order_id.x_pos_payment_ids.filtered(lambda payment:payment.state == 'draft')
        for pos_payment in pos_payment_ids:
            pos_payment.auto_payment_allocation()
        return order_id

    @api.multi
    def action_print(self):
        wb = xlwt.Workbook(encoding="UTF-8")
        date_str = str(datetime.today().date())
        ws = wb.add_sheet(date_str)
        editable = xlwt.easyxf("protection: cell_locked false;")
        read_only = xlwt.easyxf("")

        ws.col(0).width = 10 * 500
        ws.col(1).width = 10 * 1000
        ws.col(2).width = 10 * 500
        ws.col(3).width = 10 * 500
        ws.col(4).width = 10 * 500
        ws.col(5).width = 10 * 500
        ws.col(6).width = 10 * 500
        ws.col(7).width = 10 * 500
        ws.col(8).width = 10 * 500
        ws.col(9).width = 10 * 500
        ws.col(10).width = 10 * 500
        ws.col(11).width = 10 * 500
        ws.col(12).width = 10 * 500
        ws.col(13).width = 10 * 500
        ws.col(14).width = 10 * 500
        ws.col(15).width = 10 * 500
        ws.col(16).width = 10 * 500
        ws.col(17).width = 10 * 500
        ws.col(18).width = 10 * 500
        ws.col(19).width = 10 * 500

        ws.write(0, 0, u'Mã KH')
        ws.write(0, 1, u'Tên KH')
        ws.write(0, 2, u'Số ĐT1')
        ws.write(0, 3, u'SĐT 2', editable)
        ws.write(0, 4, u'NGÀY SINH', editable)
        ws.write(0, 5, u'MÃ DV CHUẨN', editable)
        ws.write(0, 6, u'Tên sản phẩm/ dịch vụ')
        ws.write(0, 7, u'DỊCH TẶNG KÈM')
        ws.write(0, 8, u"Tống số lượng sản phẩm / dịch vụ")
        ws.write(0, 9, u"Số lượng đã sử dụng(Buổi)/ ống")
        ws.write(0, 10, u"Số buổi/ ống còn lại")
        ws.write(0, 11, u"Tổng tiền")
        ws.write(0, 12, u"Số tiền đã thanh toán")
        ws.write(0, 13, u"Số tiền còn nợ")
        ws.write(0, 14, u"Ghi chú đối vs dịch vụ")
        ws.write(0, 15, u"Ngày cập nhật")


        style_content = xlwt.easyxf("align: horiz left, vert top")
        style_head_po = xlwt.easyxf('align: wrap on')
        style = xlwt.XFStyle()
        style.num_format_str = '#,##0'
        index = 3
        for line in self.transfer_therapy_ids:
            if line:
                ws.write(index, 0, line.partner_id, editable)
                ws.write(index, 1, line.partner_name, editable)
                ws.write(index, 2, line.phone, editable)
                ws.write(index, 3, line.phone_x, style)
                ws.write(index, 4, line.birthday, style)
                ws.write(index, 5, line.product_code, style)
                ws.write(index, 6, line.product_name, style)
                ws.write(index, 7, line.product_include, style)
                ws.write(index, 8, line.total_product, style)
                ws.write(index, 9, line.total_product_used, style)
                ws.write(index, 10, line.massage_actual, style)
                ws.write(index, 11, line.total_amount, style)
                ws.write(index, 12, line.total_payment, style)
                ws.write(index, 13, line.total_paid, style)
                ws.write(index, 14, line.product_note, style)
                ws.write(index, 15, line.date_update, style)
                index += 1

        stream = stringIOModule.BytesIO()
        wb.save(stream)
        xls = stream.getvalue()
        vals = {
            'name': 'Tungpd_Transfer_file.xls',
            'datas': base64.b64encode(xls),
            'datas_fname': 'Tungpd_Transfer_file.xls',
            'type': 'binary',
            'res_model': 'stock.inventory.customer.update',
            'res_id': self.id,
        }
        file_xls = self.env['ir.attachment'].create(vals)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_xls.id) + '?download=true',
            'target': 'new',
        }
