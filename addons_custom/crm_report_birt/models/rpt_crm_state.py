# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError


class RptCrmState(models.TransientModel):
    _name = 'rpt.crm.state'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    select_all_stage = fields.Boolean('All Stage')
    stage_ids = fields.Many2many('crm.stage', string="Stage")
    team_ids = fields.Many2many('crm.team', string="Team")
    select_team_all = fields.Boolean('All Team')

    @api.onchange('team_ids')
    def onchange_team(self):
        ids = []
        team_ids = self.env['crm.team'].search(
            [('team_type', 'in', ['pos', 'uid_tele'])])
        for line in team_ids:
            ids.append(line.id)
        return {
            'domain': {
                'team_ids': [('id', 'in', ids)]
            }
        }

    @api.multi
    def create_report_crm_state(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "crm_lead_state.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str3 = "&stage_id="
        param_str4 = "&team_id="
        if (self.select_all_stage == True):
            param_str3 += '0'
        else:
            list_id = ''
            for loc_id in self.stage_ids:
                list_id += ',' + str(loc_id.id)
            param_str3 += (list_id[1:])
        if (self.select_team_all == True):
            param_str4 += '0'
        else:
            list_id = ''
            for loc_id in self.team_ids:
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
    def create_report_crm_state_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "crm_lead_state.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str3 = "&stage_id="
        param_str4 = "&team_id="
        if (self.select_all_stage == True):
            param_str3 += '0'
        else:
            list_id = ''
            for loc_id in self.stage_ids:
                list_id += ',' + str(loc_id.id)
            param_str3 += (list_id[1:])
        if (self.select_team_all == True):
            param_str4 += '0'
        else:
            list_id = ''
            for loc_id in self.team_ids:
                list_id += ',' + str(loc_id.id)
            param_str4 += (list_id[1:])
        param_str = param_str1 + param_str3 + param_str4
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str+ '&__format=xlsx',
            'target': 'self',
        }

