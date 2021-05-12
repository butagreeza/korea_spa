# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, UserError
from datetime import datetime

class PosCommissionAllocation(models.Model):
    _name = 'pos.commission.allocation'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", default='/')
    date_allocation = fields.Datetime("Date Allocation", default=lambda self: fields.Datetime.now(), track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', "Partner", track_visibility='onchange')
    state = fields.Selection([('draft', "Draft"), ('to_approve', "To Approve"), ('done', "Done"), ('cancel', "Cancel")], default='draft', track_visibility='onchange')
    commission_line_ids = fields.One2many('pos.commission.allocation.line', 'commission_id', "Commission Allocation")
    account_cash_in_id = fields.Many2one('account.cash', string='Account cash In', domain=lambda self: [('type', '=', 'in')])
    account_cash_out_id = fields.Many2one('account.cash', string='Account cash Out', domain=lambda self: [('type', '=', 'out')])

    @api.onchange('order_id')
    def _onchange_order(self):
        if self.order_id:
            self.partner_id = self.order_id.partner_id.id

    @api.onchange('partner_id')
    def _onchange_partner(self):
        if self.partner_id:
            self.order_id = False

    @api.multi
    def action_send(self):
        if self.state == 'to_approve':
            raise UserError('Trạng thái của đơn phân bổ hoa hồng đã thay đổi. Vui lòng F5 để tiếp tục thao tác!')
        amount_total = 0
        arr_order = []
        for line in self.commission_line_ids:
            arr_order.append(line.order_id.id)
        for order_id in set(arr_order):
            order = self.env['pos.order'].browse(order_id)
            amount = 0
            for commission_id in self.commission_line_ids.filtered(lambda line:line.order_id.id == order_id):
                amount += commission_id.amount
                if commission_id.partner_id == self.partner_id:
                    raise UserError('Không được phân bổ hoa hồng cho khách hàng thanh toán đơn hàng!')
            if amount > order.amount_total:
                raise UserError('Số tiền đã phân bổ hoa hồng lớn hơn số tiền được phân bổ. Vui lòng kiểm tra lại!')
            amount_total += amount
        if amount_total <= 0:
            raise UserError('Không thể tạo phiếu chi 0 đồng. Vui lòng kiểm tra lại!')
        self.state = 'to_approve'

    @api.multi
    def action_confirm_allocation(self):
        if self.state == 'done':
            raise UserError('Trạng thái của đơn phân bổ hoa hồng đã thay đổi. Vui lòng F5 để tiếp tục thao tác!')
        self.state = 'done'
        #kiểm tra điều kiện đầu vào để tạo phiếu chi
        journal_id = self.env['account.journal'].search([('code', '=', 'CSH1')])
        if not journal_id:
            raise UserError('Bạn chưa cấu hình phương thức thanh toán Tiền mặt')
        product_commission = self.env['product.product'].search([('default_code', '=', 'SPHH')], limit=1)
        if not product_commission:
            raise UserError('Bạn chưa cấu hình Sản phẩm hoa hồng có tham chiếu nội bộ là SPHH! Vui lòng tạo thêm. Lưu ý cấu hình TK thu/ chi cho sản phẩm')

        cash_id = self.env['account.cash'].create({
            'type': 'out',
            'partner_id': self.partner_id.id,
            'journal_id': journal_id.id,
            'date': (datetime.now().date()).strftime('%Y-%m-%d'),
            'reason': f'Trích hoa hồng cho khách {self.partner_id.name}',
            'ref': self.name,
        })
        self.account_cash_out_id = cash_id.id
        for commission_line_id in self.commission_line_ids.filtered(lambda line:line.amount > 0):
            arr_line = []
            note = f'{commission_line_id.percent} % của {commission_line_id.amount_commission} - số tiền phân bổ hoa hồng'
            cash_id.lines = [(0, 0, ({
                    'partner_id': self.partner_id.id,
                    'product_id': product_commission.id,
                    'value': commission_line_id.amount,
                    'name': note + str(commission_line_id.note) if commission_line_id.note else '',
                    'cash_id': cash_id.id,
                    'account_id': product_commission.property_account_expense_id,
                }))]
        cash_id.action_carrying()

    @api.multi
    def action_back(self):
        if self.state != 'to_approve':
            raise UserError('Trạng thái của đơn phân bổ hoa hồng đã thay đổi. Vui lòng F5 để tiếp tục thao tác!')
        self.state = 'draft'

    @api.multi
    def action_cancel(self):
        if self.state == 'cancel':
            raise UserError('Trạng thái của đơn phân bổ hoa hồng đã thay đổi. Vui lòng F5 để tiếp tục thao tác!')
        self.state = 'cancel'
        # kiểm tra điều kiện đầu vào để tạo phiếu chi
        journal_id = self.env['account.journal'].search([('code', '=', 'CSH1')])
        if not journal_id:
            raise UserError('Bạn chưa cấu hình phương thức thanh toán Tiền mặt')
        product_commission = self.env['product.product'].search([('default_code', '=', 'SPHH')], limit=1)
        if not product_commission:
            raise UserError(
                'Bạn chưa cấu hình Sản phẩm hoa hồng có tham chiếu nội bộ là SPHH! Vui lòng tạo thêm. Lưu ý cấu hình TK thu/ chi cho sản phẩm')
        # với mỗi khách hàng sẽ tạo 1 phiếu chi ở trạng thái hoàn thành
        cash_id = self.env['account.cash'].create({
            'type': 'in',
            'partner_id': self.partner_id.id,
            'journal_id': journal_id.id,
            'date': (datetime.now().date()).strftime('%Y-%m-%d'),
            'reason': f'Hủy trích hoa hồng cho khách {self.partner_id.name}',
            'ref': self.name,
        })
        self.account_cash_in_id = cash_id.id
        for commission_line_id in self.commission_line_ids:
            arr_line = []
            note = f'{commission_line_id.percent} % của {commission_line_id.amount_commission} - số tiền phân bổ hoa hồng'
            cash_id.lines = [(0, 0, ({
                'partner_id': self.partner_id.id,
                'product_id': product_commission.id,
                'value': commission_line_id.amount,
                'name': note,
                'cash_id': cash_id.id,
                'account_id': product_commission.property_account_expense_id,
            }))]
        cash_id.action_carrying()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('pos.commission.allocation') or _('New')
        return super(PosCommissionAllocation, self).create(vals)

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm("Cảnh báo!", ("Bạn không thể xóa khi trạng thái khác tạo mới"))
        return super(PosCommissionAllocation, self).unlink()