# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, http
from datetime import datetime
from odoo.exceptions import ValidationError


class RptRevenueAllocationSumDefaultUse(models.TransientModel):
    _name = 'rpt.revenue.allocation.sum.default.use'

    def _default_employee(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee

    def _default_team_id(self):
        team_ids = self.env['crm.team']
        UserObj = http.request.env['res.users']
        group_leader_uid_telesales = UserObj.has_group('izi_res_permissions.group_leader_uid_telesales')
        group_member_uid_telesales = UserObj.has_group('izi_res_permissions.group_member_uid_telesales')
        if group_leader_uid_telesales:
            team_ids = self.env['crm.team'].search([('x_member_ids', '=', self.env.uid)], limit=1)
            return team_ids
        else:
            return False


    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    employee_id = fields.Many2many('hr.employee', string="Employee", default=_default_employee)
    crm_team_ids = fields.Many2many('crm.team', string="Team", default=_default_team_id)
    # select_all = fields.Boolean('All Team')

    @api.onchange('crm_team_ids')
    def onchange_crm_team(self):
        ids = []
        team_ids = []
        team_obj = self.env['crm.team'].search([('x_member_ids', '=', self.env.uid)])
        for x in team_obj:
            team_ids.append(x.id)
        for team in self.crm_team_ids:
            for user in team.x_member_ids:
                employee_ids = self.env['hr.employee'].search(
                    ['|', ('user_id', '=', user.id), ('x_user_ids', 'in', [user.id])])
                for id in employee_ids:
                    ids.append(id.id)
        return {
            'domain': {
                'crm_team_ids': [('id', 'in', team_ids)],
                'employee_id': [('id', 'in', ids)]
            }
        }

    @api.multi
    def create_report(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_revenue_sum_employee.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str4 = "&employee_id="
        employee_id = ''
        list_emp = ''
        if self.crm_team_ids:
            for team in self.crm_team_ids:
                for user in team.x_member_ids:
                    employee_ids = self.env['hr.employee'].search(['|', ('user_id', '=', user.id), ('x_user_ids', 'in', [user.id])])
                    for emp in employee_ids:
                        list_emp += ',' + str(emp.id)
            employee_id = (list_emp[1:])
        if self.employee_id:
            employee = ''
            for emp in self.employee_id:
                employee += ',' + str(emp.id)
            employee_id = (employee[1:])
        param_str = param_str1 + param_str4 + employee_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
            'target': 'new',
        }

    # @api.multi
    # def create_report_excel(self):
    #     param_obj = self.env['ir.config_parameter']
    #     url = param_obj.get_param('birt_url')
    #     if not url:
    #         raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
    #     report_name = "rpt_revenue_emplooyee.rptdesign"
    #     param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
    #     param_str4 = "&employee_id="
    #     employee_id = '0'
    #     if self.select_all == False:
    #         list_emp = ''
    #         if self.crm_team_ids:
    #             for team in self.crm_team_ids:
    #                 for user in team.x_member_ids:
    #                     employee_ids = self.env['hr.employee'].search(
    #                         ['|', ('user_id', '=', user.id), ('x_user_ids', 'in', [user.id])])
    #                     for emp in employee_ids:
    #                         list_emp += ',' + str(emp.id)
    #             employee_id = (list_emp[1:])
    #         if self.employee_ids:
    #             employee = ''
    #             for emp in self.employee_ids:
    #                 employee += ',' + str(emp.id)
    #             employee_id = (employee[1:])
    #     param_str = param_str1 + param_str4 + employee_id
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
    #         'target': 'self',
    #     }


