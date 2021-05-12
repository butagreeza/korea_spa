# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import UserError, ValidationError, MissingError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import except_orm, Warning as UserError


class InvoiceMakePayment(models.TransientModel):
    _inherit = 'invoice.make.payment'

    def _show_deposit_amount_residual(self):
        deposit_lines = self.env['pos.customer.deposit'].search([('partner_id', '=', self.invoice_id.partner_id.id)])
        total = 0.0
        for line in deposit_lines:
            total += line.residual
        self.deposit_amount_residual = total
        self.show_deposit_amount = True
        self.amount = min(self.deposit_amount_residual, self.amount)

    deposit_amount_residual = fields.Float("Số tiền đặt cọc", compute=_show_deposit_amount_residual, store=False)
    show_deposit_amount = fields.Boolean('Hiện đặt cọc', default=False, store=False)

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        self.show_deposit_amount = False
        self.amount = self.invoice_id.residual
        super(InvoiceMakePayment, self)._onchange_journal_id()
        if self.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
            self._show_deposit_amount_residual()

    def add_more_payment(self):
        if self.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
            deposit_lines = self.env['pos.customer.deposit'].search([('partner_id', '=', self.invoice_id.partner_id.id)])
            total = 0.0
            for line in deposit_lines:
                total += line.residual
            if self.amount > total:
                raise UserError("Số tiền thanh toán nhiều hơn số tiền đặt cọc của khách hàng.")
            elif self.amount <= 0:
                raise ValidationError("Số tiền thanh toán không hợp lệ.")
            elif self.amount > self.invoice_id.residual:
                raise UserError("Số tiền thanh toán nhiều hơn số nợ của khách hàng.")
            order_id = self.env['pos.order'].search([('name', '=', self.invoice_id.reference)], limit=1)
            # Trừ tiền đặt cọc
            self.env['pos.customer.deposit.line'].create({
                'journal_id': self.journal_id.id,
                'date': date.today(),
                'amount': self.amount,
                'order_id': order_id.id if order_id else None,
                'deposit_id': deposit_lines[0].id,
                'type': 'payment',
                'partner_id': self.invoice_id.partner_id.id,
                'state': 'done'
            })
            # deposit_lines[0].residual -= self.amount


    def process_payment(self):
        UserObj = self.env['res.users']
        user = UserObj.search([('id', '=', self._uid)], limit=1)
        residual = self.invoice_id.residual
        # Kiểm tra số tiền
        if not self.amount or self.amount <= 0:
            raise UserError("Số tiền thanh toán không hợp lệ, vui lòng kiểm tra lại!")

        # if self.x_currency_id and (self.amount < residual):
        #     raise UserError("Thanh toán ngoại tệ không thể nhỏ hơn số tiền cần thanh toán!")
        # Thanh toán = thẻ tiền
        if self.journal_id.id == self.session_id.config_id.journal_vm_id.id:
            if self.invoice_id.x_pos_order_id and self.invoice_id.x_pos_order_id.x_type not in ('1', '3'):
                raise UserError("Thẻ tiền chỉ dùng thanh toán công nợ cho dịch vụ lẻ!")
            vm_amount = self.env['pos.virtual.money'].get_available_amount_by_partner(self.invoice_id.partner_id.id)
            if not vm_amount or vm_amount < self.amount:
                raise UserError('Số dư thẻ tiền không đủ để thanh toán!')
            vm_lines = self.env['pos.virtual.money'].search(
                [('typex', '=', '1'), ('partner_id', '=', self.invoice_id.partner_id.id), ('state', '=', 'ready')],
                order='id asc')
            # Tổng tiền cần thanh toán trên dòng thanh toán
            remain = self.amount
            vm_histories = {}

            def compute_payment(line, remain, amount):
                # Nếu số tiền cần thanh toán >= số tiền còn lại trên dòng đã thanh toán
                if remain >= (line.money - line.debt_amount - line.money_used):
                    # Tổng số tiền cần thanh toán giảm = số tiền còn lại trên dòng đã thanh toán
                    remain -= line.money - line.debt_amount - line.money_used
                    # Tổng tiền ảo giảm = số tiền đã trừ
                    amount -= self.amount - remain
                    # Thêm lịch sử sử dụng tiền ảo = số tiền đã dùng
                    if line.id in vm_histories:
                        vm_histories['%s_%s' % (line.id, self.id)][
                            'amount'] += line.money - line.debt_amount - line.money_used
                    else:
                        vm_histories['%s_%s' % (line.id, self.id)] = {'vm_id': line.id,
                                                                      'amount': line.money - line.debt_amount - line.money_used,
                                                                      'order_id': self.invoice_id.x_pos_order_id.id}
                    # Dòng tiền này đã dùng hết số đã thanh toán
                    line.update({'money_used': line.money - line.debt_amount})
                # Nếu số tiền cần thanh toán < số tiền còn lại trên dòng đã thanh toán
                else:
                    # Tổng tiền cần thanh toán giảm = số tiền còn lại cần thanh toán
                    amount -= remain
                    # Thêm lịch sử sử dụng = số tiền còn lại cần thanh toán
                    if line.id in vm_histories:
                        vm_histories['%s_%s' % (line.id, self.id)]['amount'] += remain
                    else:
                        vm_histories['%s_%s' % (line.id, self.id)] = {'vm_id': line.id, 'amount': remain,
                                                                      'order_id': self.invoice_id.x_pos_order_id.id}
                    # Cập nhật tăng số tiền đã dùng = số tiền còn lại cần thanh toán
                    line.update({'money_used': line.money_used + remain})
                    remain = 0
                return remain, amount

            # Thực hiện trừ cho đến khi đủ số tiền muốn thanh toán
            for line in vm_lines:
                line_in_use = line
                # Bỏ qua các dòng thẻ tiền đã dùng hết số đã thanh toán
                if line.money - line.debt_amount == line.money_used:
                    if line.sub_amount_id and line.sub_amount_id.money - line.sub_amount_id.debt_amount > line.sub_amount_id.money_used:
                        line_in_use = line.sub_amount_id
                    else:
                        continue
                remain, vm_amount = compute_payment(line_in_use, remain, vm_amount)
                if remain and line_in_use.id == line.id and line.sub_amount_id \
                        and line.sub_amount_id.money - line.sub_amount_id.debt_amount > line.sub_amount_id.money_used:
                    line_in_use = line.sub_amount_id
                    remain, vm_amount = compute_payment(line_in_use, remain, vm_amount)
            # Ghi lịch sử sử dụng thẻ tiền
            if len(vm_histories):
                vm_history_obj = self.env['pos.virtual.money.history']
                for h in vm_histories:
                    if vm_histories[h]['amount'] != 0:
                        vm_history_obj.create(vm_histories[h])
        # Thanh toán = các phương thức khác
        self.add_more_payment()

        # Tìm mã account.bank.statement để đẩy account.bank.statement.line vào phiên
        statement_id = False
        for statement in self.session_id.statement_ids:
            if statement.journal_id.id == self.journal_id.id:
                statement_id = statement.id
                break
        if not statement_id:
            raise MissingError(_(
                'Xuất hiện một hình thức thanh toán mới không được sử dụng trong phiên làm việc của bạn, vui lòng kiểm tra lại !'))
        # Tạo account.bank.statement.line
        statement = self.env['account.bank.statement.line'].create({
            'amount': self.amount,
            'statement_id': statement_id,
            'date': date.today(),
            'name': self.invoice_id.number,
            'account_id': self.invoice_id.account_id.id,
            'partner_id': self.invoice_id.partner_id.id,
            'journal_id': self.journal_id.id,
            'x_ignore_reconcile': True,
            'ref': _('PAID_') + _(
                self.invoice_id.origin and self.invoice_id.origin or self.invoice_id.name or self.invoice_id.number),
        })
        # SangsLA thêm ngày 3/10/2018 Thêm order vào form khi chung của khách hàng

        pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search(
            [('partner_id', '=', self.invoice_id.partner_id.id), ('state', '=', 'draft'),
             ('session_id', '=', self.session_id.id)])
        if pos_sum_digital_obj:
            statement.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        else:
            pos_sum_digital_obj = self.env['pos.sum.digital.sign'].create({
                'partner_id': self.invoice_id.partner_id.id,
                'state': 'draft',
                'date': date.today(),
                'session_id': self.session_id.id,
            })
            statement.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        # het
        # Sangla them nếu thanh toán quá số tiền trong công nợ => Tự động bỏ ra đặt cọc
        # Huyen BV 9/7/2020 Không cho phép thanh toán quá số tiền
        if self.amount - self.invoice_id.residual > 0:
            raise except_orm("Cảnh báo!", ("Bạn không thể thanh toán sô tiền lớn hơn số tiền còn lại"))
            # deposit_lines = self.env['pos.customer.deposit'].search(
            #     [('partner_id', '=', self.invoice_id.partner_id.id)])
            # if not deposit_lines:
            #     Master = self.env['pos.customer.deposit']
            #     vals = {
            #         'name': self.invoice_id.partner_id.name,
            #         'partner_id': self.invoice_id.partner_id.id,
            #         'journal_id': self.session_id.config_id.journal_deposit_id.id,
            #     }
            #     deposit_lines = Master.create(vals)
            # argvs = {
            #     'journal_id': self.session_id.config_id.journal_deposit_id.id,
            #     'date': date.today(),
            #     'amount': self.amount - self.invoice_id.residual,
            #     # 'order_id': self.id,
            #     'deposit_id': deposit_lines[0].id,
            #     'type': 'deposit',
            #     'partner_id': self.invoice_id.partner_id.id,
            #     'session_id': self.session_id.id
            # }
            # deposit_id = self.env['pos.customer.deposit.line'].create(argvs)
            # deposit_id.update({'state': 'done'})
            # hết

        payment_methods = statement.journal_id.inbound_payment_method_ids
        payment_method_id = payment_methods and payment_methods[0] or False

        if self.amount - self.invoice_id.residual > 0:
            pay = self.env['account.payment'].create({
                'amount': self.invoice_id.residual,
                'journal_id': statement.journal_id.id,
                'payment_date': statement.date,
                'comunication': statement.name,
                'payment_type': 'inbound',
                'payment_method_id': payment_method_id.id,
                'invoice_ids': [(6, 0, self.invoice_id.ids)],
                'partner_type': 'customer',
                'partner_id': statement.partner_id.id,
                'x_customer_sign': self.customer_sign,
                'branch_id': user.branch_id.id,
                'x_payment_debit': True,
                'x_debt_settlement': True,
            })
            pay.with_context(izi_partner_debt=True).action_validate_invoice_payment()
            statement.x_payment_id = pay.id
        else:
            pay = self.env['account.payment'].create({
                'amount': statement.amount,
                'journal_id': statement.journal_id.id,
                'payment_date': statement.date,
                'comunication': statement.name,
                'payment_type': 'inbound',
                'payment_method_id': payment_method_id.id,
                'invoice_ids': [(6, 0, self.invoice_id.ids)],
                'partner_type': 'customer',
                'partner_id': statement.partner_id.id,
                'x_customer_sign': self.customer_sign,
                'branch_id': user.branch_id.id,
                'x_payment_debit': True,
                'x_debt_settlement': True,
            })
            pay.with_context(izi_partner_debt=True).action_validate_invoice_payment()
            statement.x_payment_id = pay.id
        # Lấy đơn hàng đã phát sinh hoá đơn
        order_id = self.env['pos.order'].search([('name', '=', self.invoice_id.reference)])
        if order_id and len(order_id) == 1:
            # Nếu Ghi nợ không ghi nhận doanh thu thì khi trả nợ phải ghi nhận
            if order_id.session_id.config_id.journal_debt_id.id not in order_id.session_id.config_id.journal_loyal_ids.ids \
                    and self.journal_id.id != self.session_id.config_id.journal_vm_id.id:
                # Tungpd chỉnh sửa phan bo doanh thu theo "cấu hình/điểm bản hàng/phân bổ doanh thu cho đơn đặt cọc" ngay 18/11
                # nếu phân bổ doanh thu cho đơn đặt cọc thì không ghi nhận doanh thu khi sử dụng cần trừ đặt coc
                if self.journal_id.id == self.session_id.config_id.journal_deposit_id.id and self.session_id.config_id.x_allocation_deposit:
                    pass
                else:
                    if self.journal_id.id in self.session_id.config_id.journal_loyal_ids.ids:
                        self._allocation_revenua(self.amount - (self.amount / 100 * self.journal_id.card_swipe_fees), order_id,
                                                     self.session_id)
                        if self.amount > 0:
                            # Ghi lich su doanh thu
                            self.env['crm.vip.customer.revenue'].create({
                                'partner_id': self.invoice_id.partner_id.id,
                                'order_id': order_id.id,
                                'journal_id': self.journal_id.id,
                                'amount': self.amount - (self.amount / 100 * self.journal_id.card_swipe_fees),
                                'date': date.today(),
                            })
                        # Cộng doanh thu cho KH
                        self.invoice_id.partner_id.update({
                            'x_loyal_total': self.invoice_id.partner_id.x_loyal_total + self.amount - (
                                        self.amount / 100 * self.journal_id.card_swipe_fees),
                            # 'x_point_total': self.invoice_id.partner_id.x_point_total + self._get_loyal_total(self.amount),
                        })
                    # loyal_total = self._get_loyal_total(self.amount)
                    # if loyal_total != 0:
                    #     self.env['izi.vip.point.history'].create({
                    #         'partner_id': self.invoice_id.partner_id.id,
                    #         'order_id': order_id.id,
                    #         'date': date.today(),
                    #         'point': loyal_total,
                    #     })
                    # Sangla Công thêm điểm cho Kh giới thiệu khách hàng
                        order = self.env['pos.order'].search([('partner_id', '=', order_id.partner_id.id)], order="id asc",
                                                             limit=1)
                    # order_len = self.env['pos.order'].search([('partner_id', '=', order_id.partner_id.x_presenter.id)])
                    # if len(order_len) == 0:
                    # if (order.id == order_id.id) and order_id.partner_id.x_presenter:
                    #     order_id.partner_id.x_presenter.update(
                    #         {'x_point_total': (self._get_loyal_total(self.amount) + order_id.partner_id.x_presenter.x_point_total)})
                    #     loyal_total = self._get_loyal_total(self.amount)
                    #     if loyal_total != 0:
                    #         self.env['izi.vip.point.history'].create({
                    #             'partner_id': order_id.partner_id.x_presenter.id,
                    #             'order_id': order_id.id,
                    #             'date': date.today(),
                    #             'point': loyal_total,
                    #         })

                        # Tiennq cong han muc ghi no cho Kh hoac nguoi so huu
                        if not order_id.x_owner_id:
                            order_id.partner_id.x_balance += self.amount
                        else:
                            order_id.x_owner_id.x_balance += self.amount


            # Cập nhật lại số tiền nợ của đơn hàng
            for line in order_id.lines:
                # Cập nhật nợ mua thẻ tiền
                if line.product_id.default_code and line.product_id.default_code.upper() == 'COIN' and line.discount != 100:
                    vm_id = self.env['pos.virtual.money'].search(
                        [('partner_id', '=', self.invoice_id.partner_id.id),
                         ('order_id', '=', order_id.id),
                         ('typex', '=', '1')])
                    if self.amount - self.invoice_id.residual > 0:
                        vm_id.update({'debt_amount': vm_id.debt_amount - vm_id.debt_amount})
                    else:
                        vm_id.update({'debt_amount': vm_id.debt_amount - self.amount})
                    if vm_id.sub_amount_id and vm_id.debt_amount == 0.0:
                        vm_id.sub_amount_id.update({'debt_amount': 0.0})

        # if not self.date_due and self.amount < self.invoice_id.residual:
        #     raise except_orm('Cảnh báo', ('Bạn phải chọn ngày thanh toán công nợ!'))
        if self.date_due:
            if self.date_due < str(date.today()):
                raise except_orm('Cảnh báo!', ('Ngày thanh toán công nợ phải lớn hơn ngày hiện tại'))
        if self.date_due:
            self.invoice_id.date_due = self.date_due

        if self.invoice_id:
            for i in self.invoice_id.activity_ids:
                i.unlink()

        # Send message về cho tư vấn co user về khách hàng thanh toán
        # self = self.sudo()
        # partner_ids = []
        # revenue_allocation = self.env['pos.revenue.allocation'].search([('order_id', '=', order_id.id)], order="id asc",
        #                                                                limit=1)
        # if revenue_allocation:
        #     for line in revenue_allocation.line_ids:
        #         if line.employee_id.user_id:
        #             if line.employee_id.user_id.partner_id:
        #                 partner_ids.append(line.employee_id.user_id.partner_id)
        # for partner in partner_ids:
        #     odoobot_id = self.env['ir.model.data'].xmlid_to_res_id("base.partner_root")
        #     channel = self.env['mail.channel.payment'].search([('partner_id', '=', partner.id)])
        #     if channel:
        #         message = _(
        #             "<br/>Ngày %s khách hàng %s thanh toán công nợ cho đơn hàng %s với số tiền là %s với hình thức là %s</b>" % (
        #             date.today().strftime("%d-%m-%Y"), order_id.partner_id.name, order_id.name,
        #             self.convert_numbers_to_text_sangla(self.amount), self.journal_id.name))
        #         channel.mail_channel_id.message_post(body=message, author_id=odoobot_id, message_type="comment",
        #                                                     subtype="mail.mt_comment")
        #     else:
        #         channel = self.env['mail.channel'].with_context({"mail_create_nosubscribe": True}).create({
        #             'channel_partner_ids': [(4, partner.id), (4, odoobot_id)],
        #             'public': 'private',
        #             'channel_type': 'chat',
        #             'email_send': False,
        #             'name': 'OdooBot'
        #         })
        #         self.env['mail.channel.payment'].create({'mail_channel_id': channel.id,
        #                                                  'partner_id': partner.id
        #                                                  })
        #         message = _(
        #             "<br/>Ngày %s khách hàng %s thanh toán công nợ cho đơn hàng %s với số tiền là %s với hình thức là %s</b>" % (
        #                 date.today().strftime("%d-%m-%Y"), order_id.partner_id.name, order_id.name,
        #                 self.convert_numbers_to_text_sangla(self.amount),
        #                 self.journal_id.name))
        #         channel.message_post(body=message, author_id=odoobot_id, message_type="comment",
        #                                     subtype="mail.mt_comment")
        # self.env.user.odoobot_state = 'onboarding_emoji'
        return statement
