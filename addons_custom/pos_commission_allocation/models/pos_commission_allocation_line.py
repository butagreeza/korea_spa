# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm, UserError

class PosCommissionAllocationLine(models.Model):
    _name = 'pos.commission.allocation.line'

    partner_id = fields.Many2one('res.partner', string='Partner')
    amount_total = fields.Float("Amount Total", related='order_id.amount_total', readonly='True')  # Tổng so tiền
    amount_commission = fields.Float("Amount Commission")
    amount = fields.Float("Amount") # Số tiền phân bổ
    commission_id = fields.Many2one('pos.commission.allocation', "Commission Allocation")
    order_id = fields.Many2one('pos.order', "Order")
    percent = fields.Float('Percent',digits=(16, 2))#, compute='_compute_percent', inverse='_inverse_percent', store=True)
    note = fields.Text('Note')

    @api.onchange('percent')
    def inverse_percent(self):
        for revenue in self:
            if revenue.percent > 100:
                raise UserError(
                    'Tỉ lệ tiền phân bổ %s vượt qua tỉ lệ tiền được phân bổ của đơn hàng! Vui lòng kiểm tra lại.' % (
                    int(revenue.percent)))
            revenue.amount = int(revenue.amount_commission * revenue.percent / 100)

    @api.onchange('amount_commission')
    def onchange_amount_commission(self):
        for revenue in self:
            revenue.inverse_percent()
            if revenue.amount_commission > revenue.amount_total:
                raise UserError(
                    'Số tiền phân bổ: %s lớn hơn số tiền: %s của đơn hàng! Vui lòng kiểm tra lại.' % (
                    int(revenue.amount_commission), int(self.amount_total)))

    @api.onchange('order_id')
    def onchange_order_id(self):
        for revenue in self:
            revenue.amount_commission = 0