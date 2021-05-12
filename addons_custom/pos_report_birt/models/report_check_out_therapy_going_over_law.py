from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm


class ReportCheckOutTherapyGoingOverLaw(models.TransientModel):
    _name = 'report.check.out.therapy.going.over.law'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")

    @api.multi
    def create_report_check_out_therapy_going_over_law(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_check_out_therapy_going_over_law.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str = param_str1
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
            'target': 'new',
        }


    @api.multi
    def create_report_check_out_therapy_going_over_law_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_check_out_therapy_going_over_law.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str = param_str1
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }