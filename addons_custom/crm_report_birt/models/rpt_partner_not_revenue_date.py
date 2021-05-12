# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError


class RPTPartnerNotRevenue(models.TransientModel):
    _name = 'rpt.partner.not.revenue.date'

    date = fields.Date("Date")
    date_default = fields.Date("Date Default", default='2018-09-01')


    @api.multi
    def create_rpt_partner_not_revenue_date(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_partner_not_revenue_date.rptdesign"
        param_str1 = "&date=" + self.date + "&date_default=" + self.date_default
        param_str = param_str1

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
    def create_rpt_partner_not_revenue_date_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_partner_not_revenue_date.rptdesign"
        param_str1 = "&date=" + self.date + "&date_default=" + self.date_default
        param_str = param_str1

        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }
