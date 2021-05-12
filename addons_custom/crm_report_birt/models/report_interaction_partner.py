from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm


class ReportInteractionPartner(models.TransientModel):
    _name = 'report.interaction.partner'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    department_ids = fields.Many2many('hr.department', string='Department')
    employee_ids = fields.Many2many('hr.employee', string='Employee')

    @api.multi
    def create_report_interaction_partner(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_inteaction_partner.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str2 = "&department_ids="
        param_str3 = "&employee_ids="
        if self.department_ids:
            department = ''
            for dep in self.department_ids:
                department += ',' + str(dep.id)
            department_id = (department[1:])
        else:
            department = ''
            for dep in self.env['hr.department'].search([]):
                department += ',' + str(dep.id)
            department_id = (department[1:])
        if self.employee_ids:
            employee = ''
            for emp in self.employee_ids:
                employee += ',' + str(emp.id)
            employee_id = (employee[1:])
        else:
            employee_id = '0'
        param_str = param_str1 + param_str2 + department_id + param_str3 + employee_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
            'target': 'new',
        }

    @api.multi
    def create_report_interaction_partner_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_inteaction_partner.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str2 = "&department_ids="
        param_str3 = "&employee_ids="
        if self.department_ids:
            department = ''
            for dep in self.department_ids:
                department += ',' + str(dep.id)
            department_id = (department[1:])
        else:
            department = ''
            for dep in self.env['hr.department'].search():
                department += ',' + str(dep.id)
            department_id = (department[1:])
        if self.employee_ids:
            employee = ''
            for emp in self.employee_ids:
                employee += ',' + str(emp.id)
            employee_id = (employee[1:])
        else:
            employee_id = '0'
        param_str = param_str1 + param_str2 + department_id + param_str3 + employee_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }