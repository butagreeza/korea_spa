# -*- coding: utf-8 -*-
from werkzeug._internal import _log
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from odoo.exceptions import except_orm, Warning as UserError


class RevenueAllocation(models.Model):
    _name = "pos.revenue.allocation"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", default="New", copy=False, track_visibility='onchange')
    order_id = fields.Many2one('pos.order', string="Order", ondelete='cascade')
    amount_total = fields.Float(string='Amount Total')
    amount_allocated = fields.Float(string='Amount allocated')
    amount_res = fields.Float(string='Amount residual')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    line_ids = fields.One2many('pos.revenue.allocation.line', 'revenue_allocation_id',
                               string="Allocation Line")
    state = fields.Selection([('draft', 'Draft'), ('close', 'Close')], 'State',
                             default='draft', track_visibility='onchange')
    partner_name = fields.Char(string=u'Tên KH')
    partner_code = fields.Char(string=u'Mã KH')
    session_id = fields.Char(string=u'Phiên', related='order_id.session_id.name', store=True)
    pos_session_id = fields.Many2one('pos.session', "Pos Session")
    partner_id = fields.Many2one('res.partner', string=u'Khách hàng')
    cash_management_id = fields.Many2one('account.cash', "Cash Management")
    type = fields.Selection(
        [('order', 'Order'), ('order_refund', 'Order Refund'), ('deposit', 'Deposit'), ('cash', 'Cash'),
         ('debt_settlement', 'Debt settlement'), ('cash_out', 'Cash Out'), ('cash_in', 'Cash_in')], string='Type')

    @api.onchange('order_id')
    def _onchange_order(self):
        if self.order_id:
            employee_id = self.env['hr.employee'].search(
                ['|', ('user_id', '=', self.order_id.user_id.id), ('x_user_ids', 'in', [self.order_id.user_id.id])])
            if len(employee_id) > 1:
                raise except_orm('Cảnh báo!',
                                 (
                                     "Một tài khoản người dùng đang gắn với 2 nhân viên. Vui lòng liên hệ với quản trị viên"))
            if employee_id.id == False:
                raise except_orm('Cảnh báo!', ("Bạn chưa gắn thông tin tài khoản cho nhân viên bán hàng"))
            self.amount_total = self.order_id.x_total_order
            self.partner_name = self.order_id.partner_id.name
            self.partner_id = self.order_id.partner_id.id
            self.partner_code = self.order_id.partner_id.x_code
            self.pos_session_id = self.order_id.session_id.id,
            self.line_ids = False
            tmp = []
            for line in self.order_id.lines:
                tmp.append({
                    'employee_id': employee_id.id,
                    'amount': 0,
                    'percent': 0,
                    'order_id': self.order_id.id,
                    'product_id': line.product_id,
                    'note': 'Default allocate'
                })
                self.line_ids = tmp

    @api.depends('line_ids.percent', 'line_ids')
    def compute_percent_line(self):
        allocated = 0.0
        for line in self.line_ids:
            if line.percent != 0:
                line.amount = (line.percent * self.amount_total) / 100
                if line.amount > self.amount_total:
                    raise UserError('Số tiền phần bổ vượt quá doanh thu của đơn hàng')
            allocated += line.amount_total
        self.amount_allocated = allocated
        self.amount_res = self.amount_total - allocated

    @api.depends('line_ids.amount', 'line_ids')
    def compute_percent_line(self):
        allocated = 0.0
        for line in self.line_ids:
            if line.amount != 0:
                line.percent = (line.amount / self.amount_total) * 100
                if line.percent > 100:
                    raise UserError('Số tiền phần bổ vượt quá doanh thu của đơn hàng')
            allocated += line.amount_total
        self.amount_allocated = allocated
        self.amount_res = self.amount_total - allocated

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pos.revenue.allocation') or _('New')
        return super(RevenueAllocation, self).create(vals)

    @api.multi
    def action_close(self):
        if len(self.line_ids) == 0:
            raise except_orm('Cảnh báo!', ("Bạn chưa cập nhật chi tiết phân bổ doanh thu"))
        amount_total = 0
        if self.amount_total > 0:
            for line in self.line_ids:
                if line.amount > self.amount_total:
                    raise except_orm("Thông báo!", (
                                "Bạn đang phân bổ cho %s quá số tiền doanh thu của đơn hàng %s > %s" % (
                        str(line.employee_id.name), str(line.amount), str(self.amount_total))))
                if line.amount < 0:
                    raise except_orm("Thông báo!", ("Bạn không thể phân bổ dưới 0"))
                amount_total += line.amount
            if round(amount_total) > round(self.amount_total):
                raise except_orm("Thông báo!", ("Bạn đang phân bổ quá số tiền doanh thu của đơn hàng %s > %s" % (
                str(amount_total), str(self.amount_total))))
            self.amount_allocated = amount_total
            self.amount_res = self.amount_total - self.amount_allocated
            if round(amount_total, 4) != self.amount_total:
                raise except_orm("Thông báo!", (
                            "Vui lòng kiểm tra lại phân bổ thanh toán theo công thức: Tổng doanh thu phân bổ (%s) phải bằng tổng doanh thu cần phân bổ (%s)"
                            % (str(round(amount_total, 4)), str(self.amount_total))))

        allo = self.env['pos.revenue.allocation.line'].search([('revenue_allocation_id', '=', self.id)])
        for line in allo:
            if line.amount == 0:
                raise except_orm("Thông báo!",
                                 ("Không phân bổ dich vụ với số tiền bằng 0, vui lòng xoá đi để tiếp tục"))
            line.order_id = self.order_id.id
        self.state = 'close'

    @api.multi
    def action_back(self):
        if self.pos_session_id.state == 'closed':
            user_id = self.env['res.users'].search([('id', '=', self._uid)])
            if not user_id.has_group('izi_res_permissions.group_leader_accountant') or not user_id.has_group(
                    'izi_res_permissions.group_leader_consultant'):
                raise UserError(
                    'Chỉ kế toán trưởng và trưởng tư vấn mới có thể thay đổi phân bổ khi phiên bán hàng đã đóng')
        allo = self.env['pos.revenue.allocation.line'].search([('revenue_allocation_id', '=', self.id)])
        for line in allo:
            line.order_id = False
        self.state = 'draft'
