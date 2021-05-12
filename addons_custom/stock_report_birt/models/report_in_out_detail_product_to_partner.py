# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm, UserError


class ReportInOutDetailProductToPartner(models.TransientModel):
    _name = 'report.in.out.detail.product.to.partner'

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    partner_ids = fields.Many2many('res.partner', string='Partner')
    picking_ids = fields.Many2many('stock.picking', string='Picking')
    product_ids = fields.Many2many('product.product', string='Product')

    @api.multi
    def create_report_in_out_product_partner(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_in_out_detail_product_to_partner.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str2 = "&partner_ids="
        param_str3 = "&picking_ids="
        param_str4 = "&product_ids="
        partner_id = '0'
        picking_id = '0'
        product_id = '0'
        if self.partner_ids:
            if len(self.partner_ids) > 10:
                raise UserError('Số lượng khách hàng không vượt quá 10 người. Vui lòng kiểm tra lại!')
            partner = ''
            for line in self.partner_ids:
                partner += ',' + str(line.id)
            partner_id = (partner[1:])
        if self.picking_ids:
            if len(self.picking_ids) > 10:
                raise UserError('Số lượng hóa đơn không vượt quá 10. Vui lòng kiểm tra lại!')
            picking = ''
            for line in self.picking_ids:
                picking += ',' + str(line.id)
            picking_id = (picking[1:])
        if self.product_ids:
            if len(self.product_ids) > 10:
                raise UserError('Số lượng dịch vụ không vượt quá 10. Vui lòng kiểm tra lại!')
            product = ''
            for line in self.product_ids:
                product += ',' + str(line.id)
            product_id = (product[1:])

        param_str = param_str1 + param_str2 + partner_id + param_str3 + picking_id + param_str4 + product_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
            'target': 'new',
        }

    @api.multi
    def create_report_in_out_product_partner_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_in_out_detail_product_to_partner.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str2 = "&partner_ids="
        param_str3 = "&picking_ids="
        param_str4 = "&product_ids="
        partner_id = '0'
        picking_id = '0'
        product_id = '0'
        if self.partner_ids:
            if len(self.partner_ids) > 10:
                raise UserError('Số lượng khách hàng không vượt quá 10 người. Vui lòng kiểm tra lại!')
            partner = ''
            for line in self.partner_ids:
                partner += ',' + str(line.id)
            partner_id = (partner[1:])
        if self.picking_ids:
            if len(self.picking_ids) > 10:
                raise UserError('Số lượng hóa đơn không vượt quá 10. Vui lòng kiểm tra lại!')
            picking = ''
            for line in self.picking_ids:
                picking += ',' + str(line.id)
            picking_id = (picking[1:])
        if self.product_ids:
            if len(self.product_ids) > 10:
                raise UserError('Số lượng dịch vụ không vượt quá 10. Vui lòng kiểm tra lại!')
            product = ''
            for line in self.product_ids:
                product += ',' + str(line.id)
            product_id = (product[1:])

        param_str = param_str1 + param_str2 + partner_id + param_str3 + picking_id + param_str4 + product_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }