from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm, UserError


class ReportPosActualDebt(models.TransientModel):
    _name = 'report.pos.actual.debt'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    partner_ids = fields.Many2many('res.partner', string='Partner')

    @api.multi
    def create_report_pos_actual_debt(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_pos_actual_debt.rptdesign"
        if not self.from_date:
            from_date = '2020-01-01'
        else:
            from_date = self.from_date
        partner_id = '0'
        param_str2 = "&partner_id="
        if self.partner_ids:
            if len(self.partner_ids) > 10:
                raise UserError('Số lượng khách hàng không vượt quá 10 người. Vui lòng kiểm tra lại!')
            partner = ''
            for line in self.partner_ids:
                partner += ',' + str(line.id)
            partner_id = (partner[1:])
        param_str1 = "&from_date=" + from_date + "&to_date=" + self.to_date
        param_str = param_str1 +  param_str2 + partner_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
            'target': 'new',
        }


    @api.multi
    def create_report_pos_actual_debt_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_pos_actual_debt.rptdesign"
        if not self.from_date:
            from_date = '2020-01-01'
        else:
            from_date = self.from_date
        partner_id = '0'
        param_str2 = "&partner_id="
        if self.partner_ids:
            if len(self.partner_ids) > 10:
                raise UserError('Số lượng khách hàng không vượt quá 10 người. Vui lòng kiểm tra lại!')
            partner = ''
            for line in self.partner_ids:
                partner += ',' + str(line.id)
            partner_id = (partner[1:])
        param_str1 = "&from_date=" + from_date + "&to_date=" + self.to_date
        param_str = param_str1 + param_str2 + partner_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }