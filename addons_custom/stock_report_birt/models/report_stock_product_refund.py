# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import ValidationError



class ReportStockProductRefund(models.TransientModel):
    _name = "report.stock.product.refund"

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")

    @api.multi
    def create_report_stock_product_refund(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_stock_product_refund.rptdesign"
        from_date = datetime.strptime(self.from_date, "%Y-%m-%d")
        to_date = datetime.strptime(self.to_date, "%Y-%m-%d")
        param_str = "&from_date=" + str(from_date) + "&to_date=" + str(to_date)
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
            'target': 'new',
        }

    @api.multi
    def create_report_stock_product_refund_ex(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_stock_product_refund.rptdesign"
        from_date = datetime.strptime(self.from_date, "%Y-%m-%d")
        to_date = datetime.strptime(self.to_date, "%Y-%m-%d")
        param_str = "&from_date=" + str(from_date) + "&to_date=" + str(to_date)
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }
