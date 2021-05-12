# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.tools import float_is_zero
from datetime import datetime, timedelta
try:
    import cStringIO as stringIOModule
except ImportError:
    try:
        import StringIO as stringIOModule
    except ImportError:
        import io as stringIOModule
import base64
import xlwt


class AccountInvoiceLineInherit(models.Model):
    _inherit = 'account.invoice.line'

    x_price_subtotal = fields.Float('Change Subtotal')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    @api.onchange('x_price_subtotal')
    def _onchange_price_subtotal(self):
        self.ensure_one()
        self.price_unit = self.x_price_subtotal / self.quantity

    # kế thừa hàm compute price có sẵn và tính lại tổng tiền
    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
                 'invoice_id.date_invoice', 'invoice_id.date')
    def _compute_price(self):
        res = super(AccountInvoiceLineInherit, self)._compute_price()
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
                                                          partner=self.invoice_id.partner_id)
        if self.x_price_subtotal:
            self.price_subtotal = self.x_price_subtotal
        else:
            self.price_subtotal = taxes['total_excluded'] if taxes else self.quantity * price
        self.price_total = taxes['total_included'] if taxes else self.price_subtotal

        return res


class AccountInvoiceInherit(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount_total',
                 'currency_id', 'company_id', 'date_invoice', 'type', 'invoice_line_ids.x_price_subtotal')
    def _compute_x_amount(self):
        round_curr = self.currency_id.round
        amount_untaxed = 0.0
        for line in self.invoice_line_ids:
            if line.x_price_subtotal == 0:
                amount_untaxed += line.price_subtotal
            else:
                amount_untaxed += line.x_price_subtotal
        self.x_amount_untaxed = amount_untaxed
        self.x_amount_tax = sum(round_curr(line.amount_total) for line in self.tax_line_ids)
        self.x_amount_total = self.x_amount_untaxed + self.amount_tax

    x_amount_untaxed = fields.Monetary(string='Untaxed Amount',
                                       store=True, readonly=True, compute='_compute_x_amount',
                                       track_visibility='always')
    x_amount_tax = fields.Monetary(string='Tax',
                                 store=True, readonly=True, compute='_compute_amount')
    x_amount_total = fields.Monetary(string='Total',
                                       store=True, readonly=True, compute='_compute_x_amount',
                                       track_visibility='always')
    x_description = fields.Text('Description')

    @api.multi
    def write(self, vals):
        if 'x_description' in vals.keys():
            if self.move_id:
                self.move_id.ref = vals.get('x_description')
        return super(AccountInvoiceInherit, self).write(vals)

    @api.onchange('x_description')
    def onchange_x_description(self):
        if self.x_description:
            if self.move_id:
                self.move_id.ref = self.move_id.ref + ' ' + self.x_description

    @api.multi
    def action_invoice_open(self):
        super(AccountInvoiceInherit, self).action_invoice_open()
        if self.x_description:
            if self.move_id:
                self.move_id.ref = self.x_description

    @api.model
    def invoice_line_move_line_get(self):
        res = []
        for line in self.invoice_line_ids:
            if not line.account_id:
                continue
            if line.quantity == 0:
                continue
            tax_ids = []
            for tax in line.invoice_line_tax_ids:
                tax_ids.append((4, tax.id, None))
                for child in tax.children_tax_ids:
                    if child.type_tax_use != 'none':
                        tax_ids.append((4, child.id, None))
            analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

            move_line_dict = {
                'invl_id': line.id,
                'type': 'src',
                'name': line.name,
                'price_unit': line.price_unit,
                'quantity': line.quantity,
                'price': line.price_subtotal if line.x_price_subtotal == 0 else line.x_price_subtotal,
                'account_id': line.account_id.id,
                'product_id': line.product_id.id,
                'uom_id': line.uom_id.id,
                'account_analytic_id': line.account_analytic_id.id,
                'analytic_tag_ids': analytic_tag_ids,
                'tax_ids': tax_ids,
                'invoice_id': self.id,
            }
            res.append(move_line_dict)
        return res

    @api.multi
    def action_print_excel(self):
        wb = xlwt.Workbook(encoding="UTF-8")
        ws = wb.add_sheet('Detail Invoice')
        editable = xlwt.easyxf("protection: cell_locked false;")
        read_only = xlwt.easyxf("")
        header_style = xlwt.easyxf("pattern: pattern solid, fore_color black; align: HORZ CENTER, VERT CENTER;font: height 280,color white;\
                                                               borders: left thin, right thin, top thin,top_color white, bottom_color white, right_color white, left_color white; pattern: pattern solid;")

        ws.col(0).width = 10 * 150
        ws.col(1).width = 10 * 500
        ws.col(2).width = 10 * 500
        ws.col(3).width = 10 * 500
        ws.col(4).width = 10 * 600
        ws.col(5).width = 10 * 250
        ws.col(6).width = 10 * 750
        ws.col(7).width = 10 * 500
        ws.col(8).width = 10 * 500
        ws.col(9).width = 10 * 500
        ws.write(0, 0, u'STT', header_style)
        ws.write(0, 1, u'Code', header_style)
        ws.write(0, 2, u'Style', header_style)
        ws.write(0, 3, u'Mã SP', header_style)
        ws.write(0, 4, u'Tên SP', header_style)
        ws.write(0, 5, u"Đơn vị", header_style)
        ws.write(0, 6, u"Tài khoản", header_style)
        ws.write(0, 7, u"SL", header_style)
        ws.write(0, 8, u"Đơn giá", header_style)
        ws.write(0, 9, u"Tổng tiền", header_style)

        editable = xlwt.easyxf("borders: left thin, right thin, top thin, bottom thin;")
        style_content = xlwt.easyxf("align: horiz right;borders: left thin, right thin, top thin, bottom thin;")
        style_head_po = xlwt.easyxf('align: wrap on')
        style = xlwt.XFStyle()
        style.num_format_str = '#,##0'
        borders = xlwt.Borders()
        borders.left = xlwt.Borders.THIN
        borders.right = xlwt.Borders.THIN
        borders.top = xlwt.Borders.THIN
        borders.bottom = xlwt.Borders.THIN
        style.borders = borders
        index = 1
        for line in self.invoice_line_ids:
            if line:
                ws.write(index, 0, index, editable)
                ws.write(index, 1, line.product_id.product_tmpl_id.x_product_code_id.name, editable)
                ws.write(index, 2, line.product_id.product_tmpl_id.x_product_style_id.name, editable)
                ws.write(index, 3, line.product_id.product_tmpl_id.default_code, editable)
                ws.write(index, 4, line.product_id.product_tmpl_id.name, editable)
                ws.write(index, 5, line.product_id.product_tmpl_id.uom_id.name, style_content)
                ws.write(index, 6, line.account_id.code, editable)
                ws.write(index, 7, line.quantity, style)
                ws.write(index, 8, line.price_unit, style)
                ws.write(index, 9, line.x_price_subtotal if line.x_price_subtotal != 0 else line.price_subtotal, style)
                index += 1

        stream = stringIOModule.BytesIO()
        wb.save(stream)
        xls = stream.getvalue()
        vals = {
            'name': 'Invoice' + '.xls',
            'datas': base64.b64encode(xls),
            'datas_fname': self.origin + '.xls',
            'type': 'binary',
            'res_model': 'account.invoice',
            'res_id': self.id,
        }
        file_xls = self.env['ir.attachment'].create(vals)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_xls.id) + '?download=true',
            'target': 'new',
        }
