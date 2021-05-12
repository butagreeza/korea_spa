# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError


class RptBirthdayPartner(models.TransientModel):
    _name = 'rpt.birthday.partner'

    from_month = fields.Selection([('01', "01"),('02', "02"),('03', "03"),('04', "04"),('05', "05"),('06', "06"),('07', "07"),('08', "08"),('09', "09"),('10', "10"),('11', "11"),('12', "12")])
    to_month = fields.Selection(
        [('01', "01"), ('02', "02"), ('03', "03"), ('04', "04"), ('05', "05"), ('06', "06"), ('07', "07"), ('08', "08"),
         ('09', "09"), ('10', "10"), ('11', "11"), ('12', "12")])
    code = fields.Char("Code")


    @api.multi
    def create_rpt_birthday_partner(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_birthday_partner.rptdesign"
        param_str1 = "&from_month=" + self.from_month + "&to_month=" + self.to_month
        param_str2 = "&code="
        if not self.code:
            param_str2 += '0'
        else:
            param_str2 += str('%' + self.code.upper().strip() + '%')
        param_str = param_str1 + param_str2

        # return {
        #     'type': 'ir.actions.act_url',
        #     'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
        #     'target': 'new',
        # }
        return {
            "type": "ir.actions.client",
            'name': 'Báo cáo',
            'tag': 'BirtViewerAction',
            'target': 'new',
            'context': {'birt_link': url + "/report/frameset?__report=report_korea/" + report_name + param_str}
        }

    @api.multi
    def create_rpt_birthday_partner_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_birthday_partner.rptdesign"
        param_str1 = "&from_month=" + self.from_month + "&to_month=" + self.to_month
        param_str2 = "&code="
        if not self.code:
            param_str2 += '0'
        else:
            param_str2 += str('%' + self.code.upper().strip() + '%')
        param_str = param_str1 + param_str2

        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }
