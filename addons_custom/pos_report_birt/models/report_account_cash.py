# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm


class ReportInOutCost(models.TransientModel):
    _name = 'report.account.cash'

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    type = fields.Selection([('in', 'In'), ('out', 'Out')], string='Type')
    product_ids = fields.Many2many('product.product', string='Product')

    @api.multi
    def create_report_account_cash(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_account_cash.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str2 = "&product_id="
        product_str = '0'
        product = ''
        if not self.type:
            type = '0'
        else:
            type = self.type
        if not self.branch_ids: raise except_orm('Thông báo', 'Chưa chọn chi nhánh!')
        for product_id in self.product_ids:
            product += ',' + str(product_id.id)
        product_str = (product[1:])
        param_str = param_str1 + "&type=" + str(type) + param_str2 + product_str
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
            'target': 'new',
        }

    @api.multi
    def create_report_account_cash_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_account_cash.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        if not self.type:
            type = '0'
        else:
            type = self.type
        param_str = param_str1 + "&type=" + str(type)
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }