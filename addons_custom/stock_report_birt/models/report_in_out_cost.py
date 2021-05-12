# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm, UserError


class ReportInOutCost(models.TransientModel):
    _name = 'report.in.out.cost'

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_src_id, required=True)
    product_ids = fields.Many2many('product.product', string='Product')
    user_ids = fields.Many2many('res.users', string='User')

    @api.multi
    def create_report_in_out_cost(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_in_out_cost.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str2 = "&product_ids="
        param_str4 = "&location_id="
        param_str3 = "&location_id_name="
        param_str5 = "&user_ids="
        product_id = '0'
        user_id = '0'
        if self.product_ids:
            if len(self.product_ids) > 10:
                raise UserError('Số lượng sản phẩm không vượt quá 10. Vui lòng kiểm tra lại!')
            product = ''
            for emp in self.product_ids:
                product += ',' + str(emp.id)
            product_id = (product[1:])
        if self.user_ids:
            if len(self.user_ids) > 10:
                raise UserError('Số lượng sản phẩm không vượt quá 10. Vui lòng kiểm tra lại!')
            user = ''
            for line in self.user_ids:
                user += ',' + str(line.id)
            user_id = (user[1:])
        param_str = param_str1 + param_str4 + str(self.location_id.id) + param_str3 + str(self.location_id.name.upper()) + param_str2 + product_id + param_str5 + user_id
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
        param_str2 = "&product_ids="
        param_str4 = "&location_id="
        param_str3 = "&location_id_name="
        param_str5 = "&user_ids="
        product_id = '0'
        user_id = '0'
        if self.product_ids:
            if len(self.product_ids) > 10:
                raise UserError('Số lượng sản phẩm không vượt quá 10. Vui lòng kiểm tra lại!')
            product = ''
            for emp in self.product_ids:
                product += ',' + str(emp.id)
            product_id = (product[1:])
        if self.user_ids:
            if len(self.user_ids) > 10:
                raise UserError('Số lượng sản phẩm không vượt quá 10. Vui lòng kiểm tra lại!')
            user = ''
            for line in self.user_ids:
                user += ',' + str(line.id)
            user_id = (user[1:])
        param_str = param_str1 + param_str4 + str(self.location_id.id) + param_str3 + str(
            self.location_id.name.upper()) + param_str2 + product_id + param_str5 + user_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }