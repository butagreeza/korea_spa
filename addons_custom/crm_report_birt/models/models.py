# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError


class RptCrmLead(models.TransientModel):
    _name = 'rpt.crm.lead'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    employee_ids = fields.Many2many('hr.employee', string="Employee")
    config_ids = fields.Many2many('pos.config', string="Pos Config")
    select_all = fields.Boolean('All Employee')
    select_config_all = fields.Boolean('All Config')

    @api.multi
    def create_report_crm_lead(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_crm_lead.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str3 = "&employee_id="
        param_str4 = "&pos_config_id="
        if (self.select_all == True):
            list_id = ''
            employee = self.env['hr.employee'].search([])
            for employee_id in employee:
                list_id += ',' + str(employee_id.id)
            param_str3 += (list_id[1:])
        else:
            list_id = ''
            for loc_id in self.employee_ids:
                list_id += ',' + str(loc_id.id)
            param_str3 += (list_id[1:])

        if (self.select_config_all == True):
            list_id = ''
            config = self.env['pos.config'].search([])
            for config_id in config:
                list_id += ',' + str(config_id.id)
            param_str4 += (list_id[1:])
        else:
            list_id = ''
            for loc_id in self.config_ids:
                list_id += ',' + str(loc_id.id)
            param_str4 += (list_id[1:])
        param_str = param_str1 + param_str3 + param_str4
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
    def create_report_crm_lead_sum(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_crm_lead_sum.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str3 = "&employee_id="
        param_str4 = "&x_pos_config_id="
        if (self.select_all == True):
            list_id = ''
            employee = self.env['hr.employee'].search([])
            for employee_id in employee:
                list_id += ',' + str(employee_id.id)
            param_str3 += (list_id[1:])
        else:
            list_id = ''
            for loc_id in self.employee_ids:
                list_id += ',' + str(loc_id.id)
            param_str3 += (list_id[1:])

        if (self.select_config_all == True):
            list_id = ''
            config = self.env['pos.config'].search([])
            for config_id in config:
                list_id += ',' + str(config_id.id)
            param_str4 += (list_id[1:])
        else:
            list_id = ''
            for loc_id in self.config_ids:
                list_id += ',' + str(loc_id.id)
            param_str4 += (list_id[1:])
        param_str = param_str1 + param_str3 + param_str4
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