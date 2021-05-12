# -*- coding: utf-8 -*-
from werkzeug._internal import _log
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from odoo.exceptions import except_orm, Warning as UserError


class RevenueAllocationLine(models.Model):
    _name = "pos.revenue.allocation.line"

    employee_id = fields.Many2one('hr.employee', string="Employee")
    amount = fields.Float(string="Amount")
    amount_total = fields.Float(string="Amount Total")
    revenue_allocation_id = fields.Many2one('pos.revenue.allocation', string="Revenue Allocation", ondelete='cascade')
    order_id = fields.Many2one('pos.order')
    percent = fields.Float('Percent', compute='_compute_percent', inverse='_inverse_percent', store=True)
    note = fields.Text('Note')
    team_id = fields.Many2one('crm.team', string="Team")
    #ngoant add them phan bo san pham
    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float(string="Quantity")

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        team_ids = []
        if self.employee_id and self.employee_id.user_id:
            teams = self.env['crm.team'].search([('x_member_ids', 'child_of', self.employee_id.user_id.id)])
            if teams:
                for team in teams:
                    team_ids.append(team.id)

        return {
            'domain': {
                'team_id': [('id', 'in', team_ids)]
            },
            'value': {
                'team_id': False
            }
        }

    # @api.onchange('amount', 'revenue_allocation_id.amount_total')
    # def _onchange_amount_total(self):
    #     for line in self:
    #         for order in line.order_id.lines:
    #             line.amount_total = order.price_subtotal_incl
    #             line.quantity = order.qty

    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     quantity = self.env['pos.order.line'].search([('order_id', '=', self.)])

    @api.onchange('percent', 'revenue_allocation_id')
    def onchange_percent(self):
        for revenue in self:
            revenue.amount = revenue.revenue_allocation_id.amount_total * revenue.percent / 100

    def _inverse_percent(self):
        for revenue in self:
            revenue.amount = revenue.revenue_allocation_id.amount_total * revenue.percent / 100

    @api.depends('amount')
    def _compute_percent(self):
        for revenue in self:
            revenue.percent =  revenue.amount / revenue.revenue_allocation_id.amount_total * 100