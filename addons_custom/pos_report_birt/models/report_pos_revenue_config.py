from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm


class ReportIncommingSpending(models.TransientModel):
    _name = 'report.pos.revenue.config'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    pos_config_id = fields.Many2one('pos.config', "Pos Config")
    source_partner = fields.Many2one('utm.source', string='Source')

    @api.multi
    def create_report_pos_revenue_config(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_pos_revenue_config.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        if self.source_partner:
            param_str2 = "&source=" + self.source_partner.name
        else:
            param_str2 = "&source=0"
        param_str = param_str1 + "&pos_config_id=" + str(self.pos_config_id.id) + "&pos_config_name=" + str(self.pos_config_id.name) + param_str2
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
            'target': 'new',
        }


    @api.multi
    def create_report_pos_revenue_config_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_pos_revenue_config.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        if self.source_partner:
            param_str2 = "&source=" + self.source_partner.name
        else:
            param_str2 = "&source=0"
        param_str = param_str1 + "&pos_config_id=" + str(self.pos_config_id.id) + "&pos_config_name=" + str(
            self.pos_config_id.name) + param_str2
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }