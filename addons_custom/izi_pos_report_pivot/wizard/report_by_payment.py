# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError, RedirectWarning, except_orm, UserError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import mute_logger
import logging


class ReportByPayment(models.TransientModel):
    _name = 'report.by.payment'

    partner_ids = fields.Many2many('res.partner', string='Partner')
    user_ids = fields.Many2many('res.users', string='User')
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")

    @api.onchange('user_ids')
    def onchange_user_ids(self):
        if self.user_ids:
            self.partner_ids = False

    def action_get_report_by_payment(self):
        lines = self.env['report.by.payment.line'].search([])
        lines.unlink()
        AccountBankStatementLine_Obj = self.env['account.bank.statement.line'].sudo()
        PosDepositLine_Obj = self.env['pos.customer.deposit.line'].sudo()
        Partner_Obj = self.env['res.partner'].sudo()
        AccountCash_Obj = self.env['account.cash'].sudo()
        AccountInvoice_Obj = self.env['account.invoice'].sudo()
        #todo xử lý điều kiện đầu vào
        if not self.date_from or not self.date_to:
            raise UserError('Yêu cầu nhập đủ ngày bắt đâù và ngày kết thúc!')
        bank_statement_line_ids = AccountBankStatementLine_Obj.search(
            [('date', '>=', self.date_from), ('date', '<=', self.date_to)])
        if self.partner_ids:
            bank_statement_line_ids = bank_statement_line_ids.filtered(
                lambda bs: bs.partner_id.id in self.partner_ids.ids)
        else:
            if self.user_ids:
                partner_ids = Partner_Obj.search([('user_id', 'in', self.user_ids.ids)])
                bank_statement_line_ids = bank_statement_line_ids.filtered(
                    lambda bs: bs.partner_id.id in partner_ids.ids)

        # todo xử lý dữ liệu
        vals = []
        for bank_statement_line_id in bank_statement_line_ids:
            if bank_statement_line_id.journal_id.id in bank_statement_line_id.create_uid.x_pos_config_id.journal_loyal_ids.ids:
                #lấy ở đơn hàng
                if bank_statement_line_id.pos_statement_id:
                    if bank_statement_line_id.pos_statement_id.state in ['paid','invoiced']:
                        vals.append({
                            'accounting_voucher': bank_statement_line_id.pos_statement_id.name,
                            'date_order': bank_statement_line_id.pos_statement_id.date_order,
                            'partner_id': bank_statement_line_id.partner_id.id,
                            'partner_code': bank_statement_line_id.partner_id.x_code,
                            'value_amount': bank_statement_line_id.amount,
                            'journal_id': bank_statement_line_id.journal_id.id,
                            'user_id': bank_statement_line_id.partner_id.user_id.id,
                            'pos_session_id': bank_statement_line_id.statement_id.pos_session_id.id,
                        })
                else:
                    #lấy ở đặt cọc hoàn tiền
                    if not bank_statement_line_id.x_ignore_reconcile:
                        pos_deposit_line_id = PosDepositLine_Obj.search([('name', '=', bank_statement_line_id.ref), ('state', '=', 'done')], limit=1)
                        if pos_deposit_line_id:
                            vals.append({
                                'accounting_voucher': pos_deposit_line_id.name,
                                'date_order': pos_deposit_line_id.date,
                                'partner_id': pos_deposit_line_id.partner_id.id,
                                'partner_code': pos_deposit_line_id.partner_id.x_code,
                                'value_amount': pos_deposit_line_id.amount - pos_deposit_line_id.charge_refund,
                                'journal_id': pos_deposit_line_id.journal_id.id,
                                'user_id': pos_deposit_line_id.user_id.id,
                                'pos_session_id': pos_deposit_line_id.session_id.id,
                            })
                    else:
                        # lấy ở thu chi
                        if not bank_statement_line_id.x_payment_id:
                            pass
                            # account_cash_id = AccountCash_Obj.search([('name', 'like', str(bank_statement_line_id.ref)), ('state', '=', 'done')], limit=1)
                            # if account_cash_id:
                            #     for cash_line in account_cash_id.lines:
                            #         vals.append({
                            #             'accounting_voucher': account_cash_id.name,
                            #             'date_order': account_cash_id.date,
                            #             'partner_id': account_cash_id.partner_id.id,
                            #             'partner_code': account_cash_id.partner_id.x_code,
                            #             'value_amount': float(cash_line.value),
                            #             'journal_id': account_cash_id.journal_id.id,
                            #             'user_id': account_cash_id.create_uid.id,
                            #             'pos_session_id': account_cash_id.session_id.id,
                            #         })
                        else:
                            # lấy ở thanh toán công nợ
                            account_invoice_id = AccountInvoice_Obj.search([('number', '=', str(bank_statement_line_id.name))], limit=1)
                            for account_payment in account_invoice_id.payment_ids.filtered(lambda ap: ap.amount == bank_statement_line_id.amount and ap.payment_date == bank_statement_line_id.date):
                                if account_payment.x_debt_settlement:
                                    vals.append({
                                        'accounting_voucher': account_payment.name,
                                        'date_order': account_payment.payment_date,
                                        'partner_id': account_invoice_id.partner_id.id,
                                        'partner_code': account_invoice_id.partner_id.x_code,
                                        'value_amount': account_payment.amount,
                                        'journal_id': account_payment.journal_id.id,
                                        'user_id': account_payment.create_uid.id,
                                        'pos_session_id': bank_statement_line_id.statement_id.pos_session_id.id,
                                    })
        # todo tạo phần tử cho bảng line
        # check mảng
        if len(vals) < 1:
            raise UserError('Không tìm thấy dữ liệu cho điều kiện đầu vào vừa nhập!')
        else:
            line_ids = []
            for val in vals:
                line_ids.append(self.env['report.by.payment.line'].create(val))
            pivot_view = self.env.ref('izi_pos_report_pivot.report_by_payment_line_pivot_view')
            tree_view = self.env.ref('izi_pos_report_pivot.report_by_payment_line_tree_view')
            context = self.env.context
            if self._context.get('type') == 'tree':
                view_id = [(tree_view.id, 'tree')]
            else:
                view_id = [(pivot_view.id, 'pivot')]
            return {
                'name': _('Báo cáo doanh thu (Tổng hợp/ Chi tiết)'),
                'type': 'ir.actions.act_window',
                'res_model': 'report.by.payment.line',
                'views': view_id,
                'context': context,
            }


class ReportByPaymentLine(models.TransientModel):
    _name = 'report.by.payment.line'

    name = fields.Char(string="Report By Payment")
    accounting_voucher = fields.Char( string='Accounting Voucher')
    date_order = fields.Datetime(string='Date Order', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Partner")
    partner_name = fields.Char(related='partner_id.name', string='Name partner', store=True)
    partner_code = fields.Char(related='partner_id.x_code', string='Partner Code', readonly=True)
    value_amount = fields.Float(string="Total amount", digits=0)
    journal_id = fields.Many2one('account.journal', string='Journal')
    user_id = fields.Many2one('res.users', string='User')
    pos_session_id = fields.Many2one('pos.session', string='Pos Session')
    note = fields.Text(string='Note')
