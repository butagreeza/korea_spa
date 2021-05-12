# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm


class ReportInOutCost(models.TransientModel):
    _name = 'report.in.out.cost'

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_src_id, required=True)

    @api.multi
    def create_report_in_out_cost(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_in_out_cost.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str = param_str1 + "&location_id=" + str(self.location_id.id) + "&location_id_name=" + str(self.location_id.name.upper())
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
            'target': 'new',
        }

    @api.multi
    def create_report_in_out_cost_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_in_out_cost.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str = param_str1 + "&location_id=" + str(self.location_id.id) + "&location_id_name=" + str(self.location_id.name)
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }