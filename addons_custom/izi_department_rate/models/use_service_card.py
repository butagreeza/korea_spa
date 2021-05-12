# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import except_orm, UserError
from datetime import date, datetime, timedelta


class UseServiceCardUsing(models.Model):
    _inherit = 'izi.service.card.using'

    department_rate_line_ids = fields.One2many('department.rate.line', 'using_id')

    @api.multi
    def action_rate_custom(self):
        # for i in self.department_rate_line_ids:
        departments = self.env['hr.department'].search([('x_can_be_rate', '=', True), ('active', '=', True)])
        department_rate_line = self.env['department.rate.line']
        if departments:
            if not self.department_rate_line_ids:
                for department in departments:
                    department_rate_line.create({
                        'using_id': self.id,
                        'department_id': department.id
                    })

        self.ensure_one()
        ctx = self.env.context.copy()
        view = self.env.ref('izi_department_rate.view_pop_up_rate_service')
        return {
            'name': ('Khách hàng xác nhận'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'izi.service.card.using',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_id': self.id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_confirm_rate(self):
        self.state = 'rate'
        res = self.env['department.rate']
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)])
        branch_id = user_id.branch_id
        for department_rate_line in self.department_rate_line_ids:
            dpm_rate = {
                'department_id': department_rate_line.department_id.id,
                'customer_rate': department_rate_line.customer_rate,
                'customer_comment': department_rate_line.customer_comment,
                'using_id': department_rate_line.using_id.id
            }
            res.create({
                'rate_time': datetime.now(),
                'partner_id': self.customer_id.id,
                'branch_id': branch_id.id,
                'line_ids': [(0, 0, dpm_rate)],
                'using_id': self.id
            })
            department_rate_line.unlink()
            # department_rate_line = self.env['department.rate.line'].search([('')])
