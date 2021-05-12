from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm, UserError


class ReportJobHandlingByDepartment(models.TransientModel):
    _name = 'report.job.handling.by.department'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    department_ids = fields.Many2many('hr.department', string='Department')
    employee_ids = fields.Many2many('hr.employee', string="Employee")
    select_emp_all = fields.Boolean('All Employee')

    @api.onchange('select_emp_all')
    def onchange_select_emp_all(self):
        if self.select_emp_all:
            self.employee_ids = self.env['hr.employee'].search([('department_id', 'in', self.department_ids.ids)])
        else:
            self.employee_ids = False

    @api.multi
    def create_report_crm_job_handling_by_department(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_handling_job_by_department.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str4 = "&employee_ids="
        param_str2 = "&department_ids="
        department_id = '0'
        employee_id = '0'
        if self.department_ids:
            department = ''
            for dep in self.department_ids:
                department += ',' + str(dep.id)
            department_id = (department[1:])
        if not self.select_emp_all and self.employee_ids:
            employee = ''
            for dep in self.employee_ids:
                if dep.resource_id.user_id:
                    employee += ',' + str(dep.resource_id.user_id.id)
            employee_id = (employee[1:])
        param_str = param_str1 + param_str4 + employee_id + param_str2 + department_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
            'target': 'new',
        }


    @api.multi
    def create_report_crm_job_handling_by_department_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_handling_job_by_department.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str4 = "&employee_ids="
        param_str2 = "&department_ids="
        department_id = '0'
        employee_id = '0'
        if self.department_ids:
            department = ''
            for dep in self.department_ids:
                department += ',' + str(dep.id)
            department_id = (department[1:])
        if not self.select_emp_all and self.employee_ids:
            employee = ''
            for dep in self.employee_ids:
                if dep.resource_id.user_id:
                    employee += ',' + str(dep.resource_id.user_id.id)
            employee_id = (employee[1:])
        param_str = param_str1 + param_str4 + employee_id + param_str2 + department_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }