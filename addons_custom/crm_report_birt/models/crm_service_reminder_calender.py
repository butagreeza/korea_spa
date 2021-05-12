# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError


class RptCrmServiceReminderCalender(models.TransientModel):
    _name = 'rpt.crm.service.reminder.calender'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    type = fields.Selection([('htkh', "HTKH"), ('nlkh', "NLKH")])
    config_id = fields.Many2many('pos.config', string="Pos Config")
    select_all_config = fields.Boolean('All Pos Config')
    employee_id = fields.Many2many('hr.employee', string="Employee")
    select_all_employee = fields.Boolean('All Employee', default=True)

    @api.multi
    def create_rpt_service_reminder_calender(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_crm_reminder_service.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date + "&type=" + self.type
        param_str2 = "&config_id="
        param_str3 = "&employee_id="
        if self.select_all_config:
            param_str2 += str(0)
        else:
            list_id = ''
            for loc_id in self.config_id:
                list_id += ',' + str(loc_id.id)
            param_str2 += (list_id[1:])
        if self.select_all_employee:
            param_str3 += str(0)
        param_str = param_str1 + param_str2 + param_str3

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
    def create_rpt_service_reminder_calender_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_crm_reminder_service.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date + "&type=" + self.type
        param_str2 = "&config_id="
        param_str3 = "&employee_id="
        if self.select_all_config:
            param_str2 += str(0)
        else:
            list_id = ''
            for loc_id in self.config_id:
                list_id += ',' + str(loc_id.id)
            param_str2 += (list_id[1:])
        if (self.select_all_employee == True):
            param_str3 += str(0)
        param_str = param_str1 + param_str2 + param_str3

        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }
