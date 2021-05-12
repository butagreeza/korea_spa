# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm, UserError


class ReportBirthdayPartner(models.TransientModel):
    _name = 'report.birthday.partner'

    date = fields.Selection(
        [('01', "01"), ('02', "02"), ('03', "03"), ('04', "04"), ('05', "05"), ('06', "06"), ('07', "07"), ('08', "08"),
         ('09', "09"), ('10', "10"), ('11', "11"), ('12', "12"), ('13', "13"), ('13', "13"), ('14', "14"), ('15', "15"),
         ('16', "16"), ('17', "17"), ('18', "18"), ('19', "19"), ('20', "20"), ('21', "21"), ('22', "22"), ('23', "23"),
         ('24', "24"), ('25', "25"), ('26', "26"), ('27', "27"), ('28', "28"), ('29', "29"), ('30', "30"), ('31', "31"),])
    month = fields.Selection(
        [('01', "01"), ('02', "02"), ('03', "03"), ('04', "04"), ('05', "05"), ('06', "06"), ('07', "07"), ('08', "08"),
         ('09', "09"), ('10', "10"), ('11', "11"), ('12', "12")])
    select_all = fields.Boolean(string="Select all")
    url_report = fields.Text(string="Url report")

    @api.constrains('month')
    def constrains_month(self):
        if self.month and self.date:
            if self.month in ('01', '02', '03', '05', '07', '08', '10', '12') and self.date == '31':
                raise UserError('Ơ! Không có ngày 31 của tháng %s. Vui lòng xem lại lịch!?' % str(self.month))
            if self.month == '02' and self.date == '30':
                raise UserError('Ơ! Không có ngày 30 của tháng 2. Vui lòng xem lại lịch!?')

    @api.multi
    def create_report(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_birthday_partner_korea.rptdesign"
        param_str1 = "&date=" + self.date
        param_str2 = "&month=" + self.month
        self.url_report = url + "/report/frameset?__report=report_korea/" + report_name + param_str1 + param_str2
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str1 + param_str2,
            'target': 'new',
        }

    @api.multi
    def create_report_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_birthday_partner_korea.rptdesign"
        param_str1 = "&date=" + self.date
        param_str2 = "&month=" + self.month
        self.url_report = url + "/report/frameset?__report=report_korea/" + report_name + param_str1 + param_str2
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str1 + param_str2 + '&__format=xlsx',
            'target': 'new',
        }
