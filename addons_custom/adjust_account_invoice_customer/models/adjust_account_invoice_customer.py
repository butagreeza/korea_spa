# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import except_orm

class AdjustAccountInvoiceCustomer(models.Model):
    _name = 'adjust.account.invoice.customer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    partner_id = fields.Many2one('res.partner', "Partner")
    date = fields.Datetime("Date", default=fields.Datetime.now)
    state = fields.Selection([('draft', "Draft"), ('done', "Done")], default='draft', track_visibility='onchange')
    adjust_account_invoice_ids = fields.One2many('adjust.account.invoice.customer.line', 'adjust_account_invoice_id', "Adjust Account Invoice")
    type = fields.Selection([('payment', "Payment"), ('invoice', "Invoice")], default='invoice')


    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Cảnh báo!', ('Không thể xóa bản ghi ở trạng thái khác mới'))
        super(AdjustAccountInvoiceCustomer, self).unlink()

    @api.onchange('partner_id')
    def _onchange_name(self):
        if self.partner_id:
            self.name = self.partner_id.name
            self.date = datetime.now()
        for line in self.adjust_account_invoice_ids:
            line.unlink()
        account_invoice = self.env['account.invoice'].search([('partner_id', '=', self.partner_id.id)])
        lines = []
        for tmp in account_invoice:
            note = ''
            for i in tmp.invoice_line_ids:
                note += i.name + '   |  '
            argvs = {
                'invoice_id': tmp.id,
                'amount_total': tmp.amount_total,
                'residual' :tmp.residual,
                'date_invoice': tmp.date_invoice,
                'note': note
            }
            lines.append(argvs)
        self.adjust_account_invoice_ids= lines

    @api.multi
    def exchange_invoice(self):
        if self.state != 'draft':
            raise except_orm("Cảnh báo!", ("Đơn điều chỉnh công nợ đã thay đổi trạng thái. Bạn cần F5 hoặc tải lại trang"))
        for line in self.adjust_account_invoice_ids:
            if line.is_adjust == True:
                if line.adjust_residual == line.residual:
                    continue
                # Điều chỉnh công nợ với số tổng số tiền điều chỉnh lớn hơn tổng số tiền trong hóa đơn
                if line.adjust_residual > line.residual:
                    invoice_ọbj = line.invoice_id.copy()
                    product_id = self.env['product.product'].search([('default_code', '=', "DCCN")], limit=1)
                    #     Cấu hình 1 dịch vụ là điều chỉnh công nợ để thêm vào line của hóa đơn, vói mã là DCCN
                    if not product_id:
                        raise except_orm("Cảnh báo!", ("Chưa cấu hình điều chỉnh công nợ. Vui lòng liên hệ Administrator"))
                    for tmp in invoice_ọbj.invoice_line_ids:
                        tmp.unlink()
                    invoice_line_id = self.env['account.invoice.line'].create({
                        'product_id': product_id.id,
                        'name': product_id.product_tmpl_id.name,
                        'account_id': self.env['account.account'].search([('code', '=', '5111')], limit=1).id,
                        'quantity': 1,
                        'uom_id': product_id.product_tmpl_id.uom_id.id,
                        'price_unit': line.adjust_residual - line.residual,
                        'price_subtotal': line.adjust_residual - line.residual,
                        'invoice_id': invoice_ọbj.id,
                    })
                    invoice_ọbj.update({
                        'comment': line.reason,
                        'type': 'out_invoice',
                    })
                    invoice_ọbj.action_invoice_open()
                    for inv in line.invoice_id:
                        movelines = inv.move_id.line_ids
                        to_reconcile_ids = {}
                        to_reconcile_lines = self.env['account.move.line']
                        for i in movelines:
                            if i.account_id.id == inv.account_id.id:
                                to_reconcile_lines += i
                                to_reconcile_ids.setdefault(i.account_id.id, []).append(i.id)
                            if i.reconciled:
                                i.remove_move_reconcile()
                        # invoice_id.action_invoice_open()
                        for tmpline in invoice_ọbj.move_id.line_ids:
                            if tmpline.account_id.id == inv.account_id.id:
                                to_reconcile_lines += tmpline
                        to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()
                # Điều chỉnh công nợ với số tổng số tiền điều chỉnh nhỏ hơn tổng số tiền trong hóa đơn
                if line.adjust_residual < line.residual:
                    invoice_ọbj = line.invoice_id.copy()
                    product_id = self.env['product.product'].search([('default_code', '=', "DCCN")], limit=1)
                    #     Cấu hình 1 dịch vụ là điều chỉnh công nợ để thêm vào line của hóa đơn, vói mã là DCCN
                    if not product_id:
                        raise except_orm("Cảnh báo!", ("Chưa cấu hình điều chỉnh công nợ. Vui lòng liên hệ Administrator"))
                    for tmp in invoice_ọbj.invoice_line_ids:
                        tmp.unlink()
                    invoice_line_id = self.env['account.invoice.line'].create({
                        'product_id': product_id.id,
                        'name': product_id.product_tmpl_id.name,
                        'account_id': self.env['account.account'].search([('code', '=', '5111')], limit=1).id,
                        'quantity': 1,
                        'uom_id': product_id.product_tmpl_id.uom_id.id,
                        'price_unit': -(line.adjust_residual - line.residual),
                        'price_subtotal': -(line.adjust_residual - line.residual),
                        'invoice_id': invoice_ọbj.id,
                    })
                    invoice_ọbj.update({
                        'comment': line.reason,
                        'type': 'out_refund',
                    })
                    invoice_ọbj.action_invoice_open()
                    for inv in line.invoice_id:
                        movelines = inv.move_id.line_ids
                        to_reconcile_ids = {}
                        to_reconcile_lines = self.env['account.move.line']
                        for j in movelines:
                            if j.account_id.id == inv.account_id.id:
                                to_reconcile_lines += j
                                to_reconcile_ids.setdefault(j.account_id.id, []).append(j.id)
                            if j.reconciled:
                                j.remove_move_reconcile()
                        # invoice_id.action_invoice_open()
                        for tmpline in invoice_ọbj.move_id.line_ids:
                            if tmpline.account_id.id == inv.account_id.id:
                                to_reconcile_lines += tmpline
                        to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()
        self.state = 'done'



    # @api.multi
    # def create_invoice(self):




class AdjustAcountInvoice(models.Model):
    _name = 'adjust.account.invoice.customer.line'

    invoice_id = fields.Many2one('account.invoice', "Invoice")
    amount_total = fields.Float("Amount Total")
    residual = fields.Float("Residual")
    date_invoice = fields.Date("Date Invoice")
    adjust_amount_total = fields.Float("Adjust Amount Total")
    adjust_residual = fields.Float("Adjust Residual")
    note = fields.Char("Note")
    adjust_account_invoice_id = fields.Many2one('adjust.account.invoice.customer', "Adjust Account Invoice", ondelete='cascade')
    reason = fields.Char("Reason")
    is_adjust =fields.Boolean("Is Adjust", default=False)




