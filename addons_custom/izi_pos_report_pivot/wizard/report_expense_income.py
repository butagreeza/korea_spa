# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, RedirectWarning, except_orm, UserError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import mute_logger
import logging

class ReportCashBook(models.TransientModel):
    _name = 'report.expense.income'

    partner_ids = fields.Many2many('res.partner', string='Partner')
    user_ids = fields.Many2many('res.users', string='User')
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")

    @api.onchange('user_ids')
    def onchange_user_ids(self):
        if self.user_ids:
            self.partner_ids = False

    def add_dic_pos_deposit(self, bill_type, account, pos_deposit_line):
        return {
            'bill_name': pos_deposit_line.name,
            'bill_type': bill_type,
            'date': pos_deposit_line.date,
            'account_expense_income': account,
            'partner_id': pos_deposit_line.partner_id.id,
            'category': pos_deposit_line.note,
            'journal_id': pos_deposit_line.journal_id.id,
            'user_id': pos_deposit_line.create_uid.id,
            'user_last_id': pos_deposit_line.write_uid.id,
            'amount': abs(pos_deposit_line.amount - pos_deposit_line.charge_refund)
        }

    def add_dic_account_cash(self, account_cash_id, account_cash_line_id):
        return {
            'bill_name': account_cash_id.name,
            'bill_type': account_cash_id.type,
            'date': account_cash_id.date,
            'account_expense_income': account_cash_line_id.product_id.name,
            'partner_id': account_cash_line_id.partner_id.id,
            'journal_id': account_cash_id.journal_id.id,
            'user_id': account_cash_id.create_uid.id,
            'user_last_id': account_cash_line_id.write_uid.id,
            'amount': account_cash_line_id.value,
            'category': account_cash_id.reason,
        }

    def add_dictionary_order(self, bill_type, account_expense_income, bank_statement_line):
        return {
            'bill_name': bank_statement_line.pos_statement_id.name,
            'bill_type': bill_type,
            'date': bank_statement_line.pos_statement_id.date_order,
            'account_expense_income': account_expense_income,
            'partner_id': bank_statement_line.partner_id.id,
            'category': bank_statement_line.pos_statement_id.name,
            'journal_id': bank_statement_line.journal_id.id,
            'user_id': bank_statement_line.statement_id.pos_session_id.create_uid.id,
            'user_last_id': bank_statement_line.statement_id.pos_session_id.write_uid.id,
            'amount': abs(bank_statement_line.amount)
        }


    def add_dic_account_invoice(self, bill_type, account, category, account_payment):
        return {
            'bill_name': account_payment.name,
            'bill_type': bill_type,
            'date': account_payment.payment_date,
            'account_expense_income': account,
            'partner_id': account_payment.partner_id.id,
            'category': category,
            'journal_id': account_payment.journal_id.id,
            'user_id': account_payment.create_uid.id,
            'user_last_id': account_payment.write_uid.id,
            'amount': account_payment.amount,
        }

    def action_get_report_expense_income(self):
        lines = self.env['report.expense.income.line'].search([])
        lines.unlink()
        AccountBankStatementLine_Obj = self.env['account.bank.statement.line'].sudo()
        AccountCash_Obj = self.env['account.cash'].sudo()
        PosDepositLine_Obj = self.env['pos.customer.deposit.line'].sudo()
        AccountPayment_Obj = self.env['account.payment'].sudo()
        vals = []
        #todo check điều kiện đầu vào
        if not self.date_from or not self.date_to:
            raise UserError('Yêu cầu nhập đủ ngày bắt đâù và ngày kết thúc!')
        if self.date_from > self.date_to:
            raise UserError('Điều kiện đầu vào không hợp lệ!')

        bank_statement_line_ids = AccountBankStatementLine_Obj.search([('date', '>=', self.date_from), ('date', '<=', self.date_to)])
        for bank_statement_line_id in bank_statement_line_ids:
            # nếu là báo cáo thu chi theo khoản mục thì không tính trong đơn hàng
            if self._context.get('expense_income_by_product'):
                pass
            #todo Trong đơn hàng
            if bank_statement_line_id.pos_statement_id \
                    and bank_statement_line_id.pos_statement_id.state in ['paid', 'invoiced']\
                    and bank_statement_line_id.journal_id.id in bank_statement_line_id.pos_statement_id.config_id.journal_loyal_ids.ids:
                if bank_statement_line_id.amount < 0:
                    bill_type = 'out'
                else:
                    bill_type = 'in'
                vals.append(self.add_dictionary_order(bill_type, 'Đơn hàng', bank_statement_line_id))
            else:
                #todo Trong đặt cọc hoàn tiền
                if not bank_statement_line_id.x_ignore_reconcile:
                    pos_deposit_line_id = PosDepositLine_Obj.search([('name', '=', bank_statement_line_id.ref),
                                                            ('state', '=', 'done')], limit=1)
                    # nếu là báo cáo thu chi theo khoản mục thì không tính trong đơn hàng
                    if self._context.get('expense_income_by_product'):
                        break
                    if pos_deposit_line_id.journal_id.id in pos_deposit_line_id.user_id.x_pos_config_id.journal_loyal_ids.ids:
                        if pos_deposit_line_id.x_type == 'cash':
                            bill_type = 'out'
                            account = 'Hoàn tiền'
                        else:
                            bill_type = 'in'
                            account = 'Đặt cọc'
                        vals.append(self.add_dic_pos_deposit(bill_type, account, pos_deposit_line_id))
                else:
                    #todo Trong account_cash
                    if not bank_statement_line_id.x_payment_id:
                        account_cash_id = AccountCash_Obj.search(
                            [('name', 'like', str(bank_statement_line_id.ref)), ('state', '=', 'done')], limit=1)
                        for account_cash_line_id in account_cash_id.lines:
                            if account_cash_id.journal_id.id in account_cash_id.session_id.config_id.journal_loyal_ids.ids:
                                vals.append(self.add_dic_account_cash(account_cash_id, account_cash_line_id))
                    #todo Trong thanh toán công nợ
                    else:
                        account_payment = AccountPayment_Obj.search(
                            [('id', '=', bank_statement_line_id.x_payment_id.id), ('state', 'in', ['posted', 'reconciled'])], limit=1)
                        # nếu là báo cáo thu chi theo khoản mục thì không tính trong đơn hàng
                        if self._context.get('expense_income_by_product'):
                            continue
                        if account_payment.x_debt_settlement and account_payment.journal_id.id in account_payment.create_uid.x_pos_config_id.journal_loyal_ids.ids:
                            vals.append(self.add_dic_account_invoice('in', 'Hóa đơn thanh toán công nợ',
                                                                     account_payment.name, account_payment))
        #todo tạo phần tử cho bảng line
        #check mảng
        if len(vals) < 1:
            raise UserError('Không tìm thấy dữ liệu cho điều kiện đầu vào vừa nhập!')
        else:
            line_ids = []
            for val in vals:
                self.env['report.expense.income.line'].create(val)
            #todo báo cáo thu chi theo khoản mục chi phí
            if self._context.get('expense_income_by_product'):
                name = 'Báo cáo thu chi theo từng khoản mục chi phí'
                pivot_view = self.env.ref('izi_pos_report_pivot.report_expense_income_by_product_line_pivot_view')
                tree_view = self.env.ref('izi_pos_report_pivot.report_expense_income_by_product_line_tree_view')
            #todo báo cáo sổ quỹ
            else:
                name = 'Báo cáo sổ quỹ'
                pivot_view = self.env.ref('izi_pos_report_pivot.report_cash_book_line_pivot_view')
                tree_view = self.env.ref('izi_pos_report_pivot.report_cash_book_line_tree_view')
            context = self.env.context
            if self._context.get('type') == 'tree':
                view_id = [(tree_view.id, 'tree')]
            else:
                view_id = [(pivot_view.id, 'pivot')]
            return {
                'name': _(name),
                'type': 'ir.actions.act_window',
                'res_model': 'report.expense.income.line',
                'views': view_id,
                'context': context,
            }


    def action_get_report_income(self):
        lines = self.env['report.expense.income.line'].search([])
        lines.unlink()
        AccountBankStatementLine_Obj = self.env['account.bank.statement.line'].sudo()
        AccountCash_Obj = self.env['account.cash'].sudo()
        AccountInvoice_Obj = self.env['account.invoice'].sudo()
        PosDepositLine_Obj = self.env['pos.customer.deposit.line'].sudo()

        if not self.date_from or not self.date_to:
            raise UserError('Yêu cầu nhập đủ ngày bắt đâù và ngày kết thúc!')
        vals = []

        bank_statement_line_ids = AccountBankStatementLine_Obj.search(
            [('date', '>=', self.date_from), ('date', '<=', self.date_to)])
        if self.partner_ids:
            bank_statement_line_ids = bank_statement_line_ids.filtered(lambda bs: bs.partner_id.id in self.partner_ids.ids)
        for bank_statement_line_id in bank_statement_line_ids:
            # todo Trong đơn hàng
            if bank_statement_line_id.journal_id.id in bank_statement_line_id.create_uid.x_pos_config_id.journal_loyal_ids.ids:
                if bank_statement_line_id.pos_statement_id and bank_statement_line_id.pos_statement_id.state in ['paid', 'invoiced']:
                    if self._context.get('income_by_journal') and bank_statement_line_id.amount > 0:
                        vals.append(self.add_dictionary_order('in', 'Đơn hàng', bank_statement_line_id))
                else:
                    # todo Trong đặt cọc hoàn tiền
                    if not bank_statement_line_id.x_ignore_reconcile:
                        pos_deposit_line_id = PosDepositLine_Obj.search([('name', '=', bank_statement_line_id.ref),
                                                                ('state', '=', 'done')], limit=1)
                        if pos_deposit_line_id.journal_id.id in pos_deposit_line_id.user_id.x_pos_config_id.journal_loyal_ids.ids:
                            if not self._context.get('income_by_journal') and pos_deposit_line_id.x_type == 'cash':
                                bill_type = 'out'
                                account = 'Hoàn tiền'
                                vals.append(self.add_dic_pos_deposit(bill_type, account, pos_deposit_line_id))
                            elif self._context.get('income_by_journal') and pos_deposit_line_id.x_type == 'deposit':
                                bill_type = 'in'
                                account = 'Đặt cọc'
                                vals.append(self.add_dic_pos_deposit(bill_type, account, pos_deposit_line_id))
                    else:
                        # todo Trong account_cash
                        if not bank_statement_line_id.x_payment_id:
                            account_cash_id = AccountCash_Obj.search(
                                [('name', 'like', str(bank_statement_line_id.ref)), ('state', '=', 'done')], limit=1)
                            if self.partner_ids:
                                account_cash_ids = account_cash_ids.filtered(
                                    lambda bs: bs.partner_id.id in self.partner_ids.ids)
                            if account_cash_id.journal_id.id in account_cash_id.session_id.config_id.journal_loyal_ids.ids:
                                for account_cash_line_id in account_cash_id.lines:
                                    if self._context.get('income_by_journal') and account_cash_id.type == 'in':
                                        vals.append(self.add_dic_account_cash(account_cash_id, account_cash_line_id))
                                    elif not self._context.get('income_by_journal') and account_cash_id.type != 'in':
                                        vals.append(self.add_dic_account_cash(account_cash_id, account_cash_line_id))
                        else:
                            # todo Trong thanh toán công nợ
                            account_invoice_id = AccountInvoice_Obj.search(
                                [('number', '=', str(bank_statement_line_id.name))], limit=1)
                            if self.partner_ids:
                                account_invoice_ids = account_invoice_ids.filtered(
                                    lambda bs: bs.partner_id.id in self.partner_ids.ids)
                            # nếu là báo cáo chi theo người nhận thì không dùng
                            for account_payment in account_invoice_id.payment_ids.filtered(
                                    lambda ap: ap.payment_date >= self.date_from and ap.payment_date <= self.date_to and ap.state in ['posted', 'sent', 'reconciled'] and ap.payment_type == 'outbound'):
                                if account_payment.x_debt_settlement and account_payment.journal_id.id in account_payment.create_uid.x_pos_config_id.journal_loyal_ids.ids:
                                    vals.append(self.add_dic_account_invoice('in', 'Hóa đơn thanh toán công nợ',
                                                                             account_invoice_id,
                                                                             account_payment))

        #todo tạo phần tử cho bảng line
        if len(vals) < 1:
            raise UserError('Không tìm thấy dữ liệu cho điều kiện đầu vào vừa nhập!')
        else:
            line_ids = []
            for val in vals:
                line_ids.append(self.env['report.expense.income.line'].create(val).id)
            # todo báo cáo thu theo từng loại tiền
            if self._context.get('income_by_journal'):
                name = 'Báo cáo tiền thu theo từng loại tiền'
                pivot_view = self.env.ref('izi_pos_report_pivot.report_income_by_journal_line_pivot_view')
                tree_view = self.env.ref('izi_pos_report_pivot.report_income_by_journal_line_tree_view')
            # todo báo cáo tiền chi theo đối tượng nhận
            else:
                name = 'Báo cáo tiền chi theo đuối tượng nhận'
                pivot_view = self.env.ref('izi_pos_report_pivot.report_expense_by_partner_line_pivot_view')
                tree_view = self.env.ref('izi_pos_report_pivot.report_expense_by_partner_line_tree_view')
            context = self.env.context
            if self._context.get('type') == 'tree':
                view_id = [(tree_view.id, 'tree')]
            else:
                view_id = [(pivot_view.id, 'pivot')]
            return {
                'name': _(name),
                'type': 'ir.actions.act_window',
                'res_model': 'report.expense.income.line',
                'views': view_id,
                'res_id': line_ids,
                'context': context,
            }


class ReportCashBookLine(models.TransientModel):
    _name = 'report.expense.income.line'

    name = fields.Char(string="Report Cash Book")
    bill_type = fields.Selection([('in', 'In'), ('out', 'Out')], string='Type', default='in')
    date = fields.Datetime(string='Date', help='Ngày chứng từ')
    bill_name = fields.Char(string='Bill Name', help='Số phiếu')
    account_expense_income = fields.Text(string='Account Expense Income', help='Khoản thu chi')
    category = fields.Text(string='Category')
    partner_id = fields.Many2one('res.partner', string='Partner')
    partner_name = fields.Char(related='partner_id.name', string='Name partner', store=True)
    partner_code = fields.Char(string='Code Partner', related='partner_id.x_code', readonly=True)
    journal_id = fields.Many2one('account.journal', string='Journal')
    user_id = fields.Many2one('res.users', string='User', help='Người lập')
    user_last_id = fields.Many2one('res.users', string='Last User', help='Người sửa cuối cùng')
    amount = fields.Float(string='Amount')