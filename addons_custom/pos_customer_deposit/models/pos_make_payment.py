# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, MissingError, ValidationError, except_orm
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    # def _default_amount(self):
    #     active_id = self.env.context.get('active_id')
    #     if active_id:
    #         order = self.env['pos.order'].browse(active_id)
    #         return (order.amount_total - order.amount_paid)
    #     return False

    pos_customer_deposit_line_id = fields.Many2one('pos.customer.deposit.line', string='Pos customer deposit line')
    # amount_payment = fields.Float(digits=(16, 2), required=True, default=_default_amount)

    # @api.model
    # def default_get(self, fields):
    #     a = fields
    #     res = super(PosMakePayment, self).default_get(fields)
    #     pos_customer_deposit_line_id = self._context.get('active_id')
    #     pos_customer_deposit_line = self.env['pos.customer.deposit.line'].browse(pos_customer_deposit_line_id)
    #     res['amount'] = pos_customer_deposit_line.amount_actual
    #     return res


    @api.onchange('pos_customer_deposit_line_id')
    def onchange_pos_customer_deposit_line_id(self):
        if self.pos_customer_deposit_line_id:
            self.amount = self.pos_customer_deposit_line_id.amount_actual

    def action_deposit(self):
        for payment in self:
            if self.state != 'confirm':
                return True
            DepositObj = self.env['pos.customer.deposit']
            deposit_id = DepositObj.search([('partner_id', '=', self.partner_id.id)], limit=1)
            # if self.type == 'deposit':
            #     if not deposit_id:
            #         if not self.session_id.config_id.journal_deposit_id:
            #             raise except_orm('Cảnh báo!', ("Điểm bán hàng của bạn chưa cấu hình phương thức ghi nhận đặt cọc"))
            #         vals = {
            #             'name': self.partner_id.name,
            #             'partner_id': self.partner_id.id,
            #             'journal_id': self.session_id.config_id.journal_deposit_id.id,
            #         }
            #         master_id = DepositObj.create(vals)
            #         self.deposit_id = master_id.id
            #     else:
            #         self.deposit_id = deposit_id.id
            #     if not self.deposit_id.journal_id.default_credit_account_id: raise except_orm('Thông báo', 'Sổ nhật ký %s chưa cấu hình tài khoản ghi có mặc định!' % (str(self.deposit_id.journal_id.name),))
            #     if not self.deposit_id.journal_id.default_debit_account_id: raise except_orm('Thông báo', 'Sổ nhật ký %s chưa cấu hình tài khoản ghi nợ mặc định!' % (str(self.deposit_id.journal_id.name),))
            #
            #     # datcoc
            #     move_lines = []
            #     credit_move_vals = {
            #         'name': self.name,
            #         'account_id': self.deposit_id.journal_id.default_credit_account_id.id,
            #         'credit': self.amount,
            #         'debit': 0.0,
            #         'partner_id': self.partner_id.id,
            #     }
            #     debit_move_vals = {
            #         'name': self.name,
            #         'account_id': self.journal_id.default_debit_account_id.id,
            #         'credit': 0.0,
            #         'debit': self.amount,
            #         'partner_id': self.partner_id.id,
            #     }
            #     move_lines.append((0, 0, debit_move_vals))
            #     move_lines.append((0, 0, credit_move_vals))
            #     vals_account = {
            #         'date': fields.Datetime.now(),
            #         'ref': self.name,
            #         'journal_id': self.journal_id.id,
            #         'line_ids': move_lines
            #     }
            #     move_id = self.env['account.move'].create(vals_account)
            #     move_id.post()
            # else:
            #     if not self.deposit_id.journal_id.default_credit_account_id: raise except_orm('Thông báo', 'Sổ nhật ký %s chưa cấu hình tài khoản ghi có mặc định!' % (str(self.deposit_id.journal_id.name),))
            #     if not self.deposit_id.journal_id.default_debit_account_id: raise except_orm('Thông báo', 'Sổ nhật ký %s chưa cấu hình tài khoản ghi nợ mặc định!' % (str(self.deposit_id.journal_id.name),))
            #     # hoantien
            #     move_lines = []
            #     debit_move_vals = {
            #         'name': self.name,
            #         'account_id': self.deposit_id.journal_id.default_debit_account_id.id,
            #         'debit': self.amount,
            #         'credit': 0.0,
            #         'partner_id': self.partner_id.id,
            #     }
            #     credit_move_vals = {
            #         'name': self.name,
            #         'account_id': self.journal_id.default_credit_account_id.id,
            #         'debit': 0.0,
            #         'credit': self.amount,
            #         'partner_id': self.partner_id.id,
            #     }
            #     move_lines.append((0, 0, debit_move_vals))
            #     move_lines.append((0, 0, credit_move_vals))
            #     vals_account = {
            #         'date': fields.Datetime.now(),
            #         'ref': self.name,
            #         'journal_id': self.journal_id.id,
            #         'line_ids': move_lines
            #     }
            #     move_id = self.env['account.move'].create(vals_account)
            #     move_id.post()
            # self.deposit_id.account_move_ids = [(4, move_id.id)]
            # # tạo account.bank.statement.line
            # statement_id = False
            # for statement in self.session_id.statement_ids:
            #     if statement.id == statement_id:
            #         journal_id = statement.journal_id.id
            #         break
            #     elif statement.journal_id.id == self.journal_id.id:
            #         statement_id = statement.id
            #         break
            # company_cxt = dict(self.env.context, force_company=self.journal_id.company_id.id)
            # account_def = self.env['ir.property'].with_context(company_cxt).get('property_account_receivable_id',
            #                                                                     'res.partner')
            # account_id = self.partner_id.property_account_receivable_id.id or (account_def and account_def.id) or False
            # amount = self.amount
            # amount_currency = self.x_money_multi
            # if self.type == 'cash':
            #     amount = -(self.amount - self.charge_refund)
            #     amount_currency = self.rate_vn and (amount / self.rate_vn) or 0
            # argvs = {
            #     'ref': self.name,
            #     'name': 'Deposit',
            #     'partner_id': self.partner_id.id,
            #     'amount': amount,
            #     'account_id': account_id,
            #     'statement_id': statement_id,
            #     'journal_id': self.journal_id.id,
            #     'date': self.date,
            #     'x_amount_currency': amount_currency,
            #     'x_currency_id': self.x_currency_id.id,
            # }
            # pos_make_payment_id = self.env['account.bank.statement.line'].create(argvs)
