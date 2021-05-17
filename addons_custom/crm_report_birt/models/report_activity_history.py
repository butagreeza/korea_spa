from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm


class ReportActivityHistory(models.TransientModel):
    _name = 'report.activity.history'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    department_ids = fields.Many2many('hr.department', string='Department')
    user_ids = fields.Many2many('res.users', string='User')

    @api.multi
    def create_report_crm_activity_history(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_activity_history.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str3 = "&user_id="
        param_str4 = "&department_id="
        department_id = '0'
        user_id = '0'
        if self.user_ids:
            user = ''
            for user_id in self.user_ids:
                user += ',' + str(user_id.id)
            user_id = (user[1:])
        if self.department_ids:
            department = ''
            for dep in self.department_ids:
                department += ',' + str(dep.id)
            department_id = (department[1:])

        param_str = param_str1 + param_str4 + department_id + param_str3 + user_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
            'target': 'new',
        }


    @api.multi
    def create_report_crm_activity_history_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_activity_history.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str3 = "&user_id="
        param_str4 = "&department_id="
        department_id = '0'
        user_id = '0'
        if self.user_ids:
            user = ''
            for user_id in self.user_ids:
                user += ',' + str(user_id.id)
            user_id = (user[1:])
        if self.department_ids:
            department = ''
            for dep in self.department_ids:
                department += ',' + str(dep.id)
            department_id = (department[1:])

        param_str = param_str1 + param_str4 + department_id + param_str3 + user_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }