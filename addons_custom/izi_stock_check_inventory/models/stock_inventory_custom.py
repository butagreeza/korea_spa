# -*- coding: utf-8 -*-

from odoo import fields, models, api,_
from datetime import datetime, timedelta
from odoo.osv import osv
from odoo.exceptions import except_orm, UserError
try:
    import cStringIO as stringIOModule
except ImportError:
    try:
        import StringIO as stringIOModule
    except ImportError:
        import io as stringIOModule
import base64
import xlwt
import xlrd
from datetime import date, datetime
import sys
from collections import OrderedDict

class StockInventoryCustom(models.Model):
    _inherit = 'stock.inventory'

    @api.model
    def _default_warehouse_id(self):
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.id
        else:
            raise UserError(_('You must define a warehouse for the company: %s.') % (company_user.name,))

    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse",default=_default_warehouse_id)
    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    @api.onchange('warehouse_id')
    def _onchange_location(self):
        kip = []
        if self.warehouse_id:
            view_location_id = self.warehouse_id.view_location_id.id
            location_id = self.env['stock.location'].search(
                [('usage', '=', 'internal'), ('location_id', '=', view_location_id)])
            for locat in location_id:
                kip.append(locat.id)
            self.location_id = location_id[0].id
        return {
            'domain': {'location_id': [('id', 'in', kip)]}
        }

    @api.multi
    def action_import_line(self):
        if self.field_binary_name is None:
            raise except_orm('Cảnh báo', 'Không tìm thấy file import. Vui lòng chọn lại file import.')
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise osv.except_osv("Cảnh báo!",
                                     (
                                         "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 4
            lines = []
            stock_inventory_line_obj = self.env['stock.inventory.line']
            while index < sheet.nrows:
                product_code = sheet.cell(index, 0).value
                product_obj = self.env['product.product'].search([('default_code', '=', product_code)])
                if product_obj.id == False:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại sản phẩm có mã " + str(
                                         product_code) + ". Vui lòng kiểm tra lại dòng " + str(
                                         index + 1)))
                else:
                    if product_obj[0].type == 'service':
                        raise except_orm('Cảnh báo!',
                                         ("Sản phẩm có " + str(
                                             product_code) + " là dịch vụ. Vui lòng kiểm tra lại dòng " + str(
                                             index + 1)))
                    product_id = product_obj[0].id
                    uom_id = product_obj[0].product_tmpl_id.uom_id.id
                product_qty = sheet.cell(index, 4).value
                theoretical_qty = sheet.cell(index, 3).value
                note = sheet.cell(index, 5).value
                # lot_name = str(sheet.cell(index, 3).value.split())
                # if len(lot_name) or lot_name != '' or lot_name != False:
                #     inventory_line_id = stock_inventory_line_obj.search([('inventory_id','=',self.id),('product_id','=',product_id),('product_uom_id','=',uom_id),
                #                                                             ('prod_lot_id.name','=',lot_name),('location_id','=',self.location_id.id)])
                # else:
                inventory_line_id = stock_inventory_line_obj.search(
                    [('inventory_id', '=', self.id), ('product_id', '=', product_id),
                     ('product_uom_id', '=', uom_id),('location_id', '=', self.location_id.id)])
                if len(inventory_line_id) == 0:
                    # if len(lot_name) or lot_name != '' or lot_name != False:
                    #     lot = self.env['stock.production.lot'].search([('name','=',lot_name),('product_id','=',product_id)])
                    #     if lot.id == False:
                    #         lot_id = self.env['stock.production.lot'].create({'name': lot_name, 'product_id': product_id})
                    #     else:
                    #         lot_id = lot
                    #     argvs = {
                    #         'product_id': product_id,
                    #         'product_uom_id': uom_id,
                    #         'location_id': self.location_id.id,
                    #         'prod_lot_id': lot_id.id,
                    #         'product_qty': product_qty,
                    #         'inventory_id': self.id
                    #     }
                    #     stock_inventory_line_obj.create(argvs)
                    # else:
                    argvs = {
                        'product_id': product_id,
                        'product_uom_id': uom_id,
                        'location_id': self.location_id.id,
                        'product_qty': product_qty,
                        'inventory_id': self.id,
                        'x_note': note,
                    }
                    stock_inventory_line_obj.create(argvs)
                else:
                    inventory_line_id = inventory_line_id[0]
                    inventory_line_id.update({
                        'product_qty': product_qty,
                        'x_note': note,
                    })
                index = index + 1
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    @api.multi
    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/izi_stock_check_inventory/static/template/import_izi_stock_inventory.xlsx',
            "target": "_parent",
        }

    @api.multi
    def action_print_check_inventory(self):
        self.ensure_one()
        if len(self.line_ids) < 1:
            raise UserError('Không có dữ liệu để in! Vui lòng kiểm tra lại')
        wb = xlwt.Workbook(encoding="UTF-8")
        ws = wb.add_sheet("Sản phẩm")
        editable = xlwt.easyxf("align: HORZ CENTER, VERT CENTER;font: height 280;" \
                               "borders: left thin, right thin, top dotted, bottom dotted;")
        read_only = xlwt.easyxf("")

        # Style header
        header_style = xlwt.easyxf("pattern: pattern solid,fore_color gray25; align: HORZ CENTER, VERT CENTER;font: height 280, color black, bold 1;\
                                            borders: left thin, right thin, top thin, bottom thin,top_color black, bottom_color black, right_color black, left_color black; pattern: pattern solid;")

        header_style_category = xlwt.easyxf("pattern: pattern solid,fore_color blue; align: HORZ CENTER, VERT CENTER;font: height 280, color white, bold 1;\
                                            borders: left thin, right thin, top thin, bottom thin,top_color black, bottom_color black, right_color black, left_color black; pattern: pattern solid;")

        # Width
        ws.col(0).width = 8 * 256
        ws.col(1).width = 40 * 256
        ws.col(2).width = 10 * 256
        ws.col(3).width = 30 * 256
        ws.col(4).width = 20 * 256
        ws.col(5).width = 20 * 256
        ws.col(6).width = 20 * 256
        ws.col(7).width = 40 * 256
        # Lable
        ws.write_merge(0, 0, 0, 7, 'KOREA', header_style_category)
        ws.write_merge(1, 1, 0, 7, 'Bản kiểm kho: Kho 100 TRIỆU VIỆT VƯƠNG', header_style_category)
        ws.write(4, 0, _('STT'), header_style)
        ws.write(4, 1, _('SẢN PHẨM'), header_style)
        ws.write(4, 2, _('ĐƠN VỊ'), header_style)
        ws.write(4, 3, _("ĐỊA ĐIỂM"), header_style)
        ws.write(4, 4, _("SL LÝ THUYẾT"), header_style)
        ws.write(4, 5, _("SL THỰC TẾ"), header_style)
        ws.write(4, 6, _("CHÊNH LỆCH"), header_style)
        ws.write(4, 7, _("GHI CHÚ"), header_style)

        style_total = xlwt.XFStyle()
        style_total.num_format_str = '#,##0'
        font = xlwt.Font()
        font.height = 280
        font.bold = True
        style_total.font = font
        borders = xlwt.Borders()
        borders.left = xlwt.Borders.THIN
        borders.right = xlwt.Borders.THIN
        borders.top = xlwt.Borders.THIN
        borders.bottom = xlwt.Borders.THIN
        style_total.borders = borders

        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        alignment.vert = xlwt.Alignment.VERT_CENTER
        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        pattern.pattern_fore_colour = xlwt.Style.colour_map['coral']
        style_total.pattern = pattern
        style_total.alignment = alignment

        style_content = xlwt.XFStyle()
        style_content.num_format_str = '#,##0'
        font_content = xlwt.Font()
        font_content.height = 280
        style_content.font = font_content
        borders = xlwt.Borders()
        borders.left = xlwt.Borders.THIN
        borders.right = xlwt.Borders.THIN
        borders.top = xlwt.Borders.DOTTED
        borders.bottom = xlwt.Borders.DOTTED
        style_content.borders = borders
        style_content.alignment = alignment

        index_master = 1
        stt_master = 1
        stt_detail = 5
        for product in self.line_ids:
            qty_deviation = product.theoretical_qty - product.product_qty
            ws.write(stt_detail, 0, stt_master, editable)
            ws.write(stt_detail, 1, product.product_id.name, editable)
            ws.write(stt_detail, 2, product.product_uom_id.name, style_content)
            ws.write(stt_detail, 3, product.location_id.name, style_content)
            ws.write(stt_detail, 4, product.theoretical_qty, style_content)
            ws.write(stt_detail, 5, product.product_qty, style_content)
            ws.write(stt_detail, 6, abs(qty_deviation), editable)
            if qty_deviation < 0:
                note = 'Hệ thống đang thiếu'
            else:
                note = 'Hệ thống đang thừa'

            ws.write(stt_detail, 7, note or '', editable)
            stt_detail += 1
            stt_master += 1

        # ws.write(index_master, 2, sum_quantity, header_style_category)
        # ws.write(index_master, 4, sum_discount, style_total)
        # ws.write(index_master, 5, sum_amount_total, style_total)
        stt_master += 1
        # index_master += count_master_index

        stream = stringIOModule.BytesIO()
        wb.save(stream)
        xls = stream.getvalue()
        vals = {
            'name': str(date.today().strftime("%d-%m-%Y")) + '.xls',
            'datas': base64.b64encode(xls),
            'datas_fname': _('Kiểm kê kho ')+ self.location_id.name + '_' + str(date.today().strftime("%d-%m-%Y")) + '.xls',
            'type': 'binary',
            'res_model': 'stock.inventory',
            'res_id': self.id,
        }
        file_xls = self.env['ir.attachment'].create(vals)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_xls.id) + '?download=true',
            'target': 'new',
        }
