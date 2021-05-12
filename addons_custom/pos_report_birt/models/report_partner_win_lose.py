from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm


class ReportPartnerWinLose(models.TransientModel):
    _name = 'report.partner.win.lose'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    user_id = fields.Many2one('res.users', string='User')

    @api.multi
    def create_report_partner_win_lose(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_partner_win_lose.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        if self.user_id:
            param_str2 = "&user_id=" + str(self.user_id.id)
        else:
            param_str2 = "&user_id=0"
        param_str = param_str1 + param_str2
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
            'target': 'new',
        }


    @api.multi
    def create_report_partner_win_lose_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_partner_win_lose.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        if self.user_id:
            param_str2 = "&user_id=" + str(self.user_id.id)
        else:
            param_str2 = "&user_id=0"
        param_str = param_str1 + param_str2
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }