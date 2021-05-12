# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm, UserError


class ReportCommissionToPartner(models.TransientModel):
    _name = 'report.commission.to.partner'

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    partner_ids = fields.Many2many('res.partner', string='Partner')

    @api.multi
    def create_report_commission_to_partner(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_commission_allocation.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str3 = "&partner_ids="
        partner_id = '0'
        if self.partner_ids:
            if len(self.partner_ids) > 10:
                raise UserError('Số lượng khách hàng không vượt quá 10 người. Vui lòng kiểm tra lại!')
            partner = ''
            for line in self.partner_ids:
                partner += ',' + str(line.id)
            partner_id = (partner[1:])
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str1 + param_str3 + partner_id,
            'target': 'new',
        }

    @api.multi
    def create_report_commission_to_partner_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_commission_allocation.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str3 = "&partner_ids="
        partner_id = '0'
        if self.partner_ids:
            if len(self.partner_ids) > 10:
                raise UserError('Số lượng khách hàng không vượt quá 10 người. Vui lòng kiểm tra lại!')
            partner = ''
            for line in self.partner_ids:
                partner += ',' + str(line.id)
            partner_id = (partner[1:])
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str1 + param_str3 + partner_id + '&__format=xlsx',
            'target': 'self',
        }