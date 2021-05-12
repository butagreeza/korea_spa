from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm


class ReportIncommingSpending(models.TransientModel):
    _name = 'report.incomming.spending'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    pos_config_id = fields.Many2one('pos.config', "Pos Config")

    @api.multi
    def create_report_incomming_spending(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_incomming_spending.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str = param_str1 + "&pos_config_id=" + str(self.pos_config_id.id) + "&pos_config_name=" + str(self.pos_config_id.name)
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
            'target': 'new',
        }


    @api.multi
    def create_report_incomming_spending_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_incomming_spending.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str = param_str1 + "&pos_config_id=" + str(self.pos_config_id.id) + "&pos_config_name=" + str(self.pos_config_id.name)
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }