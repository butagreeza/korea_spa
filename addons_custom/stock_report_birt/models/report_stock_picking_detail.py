# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import ValidationError, UserError



class ReportStockPickingDetail(models.TransientModel):
    _name = "report.stock.picking.detail"

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    partner_ids = fields.Many2many('res.partner', string='Partner')
    product_ids = fields.Many2many('product.product', string='Product')

    # @api.onchange('rpt_location_id')
    # def onchange_location(self):
    #     if self._uid != 1:
    #         list = []
    #         user_obj = self.env['res.users'].search([('id', '=', self._uid)])
    #         locations = self.env['stock.location'].search(
    #             [('branch_id', 'in', user_obj.branch_ids.ids), ('usage', '=', 'internal')])
    #         for location_id in locations:
    #             list.append(location_id.id)
    #         return {
    #             'domain': {'rpt_location_id': [('id', 'in', list)]}
    #         }

    @api.multi
    def create_report_stock_picking_detail(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_stock_picking_detail.rptdesign"
        from_date = datetime.strptime(self.from_date, "%Y-%m-%d").date()
        to_date = datetime.strptime(self.to_date, "%Y-%m-%d").date()
        param_str1 = "&from_date=" + str(from_date) + "&to_date=" + str(to_date)
        param_str2 = "&product_ids="
        param_str3 = "&partner_ids="
        partner_id = '0'
        product_id = '0'
        if self.product_ids:
            if len(self.product_ids) > 10:
                raise UserError('Số lượng sản phẩm không vượt quá 10. Vui lòng kiểm tra lại!')
            product = ''
            for emp in self.product_ids:
                product += ',' + str(emp.id)
            product_id = (product[1:])
        if self.partner_ids:
            if len(self.partner_ids) > 10:
                raise UserError('Số lượng khách hàng không vượt quá 10 người. Vui lòng kiểm tra lại!')
            partner = ''
            for line in self.partner_ids:
                partner += ',' + str(line.id)
            partner_id = (partner[1:])
        param_str = param_str1 + param_str2 + product_id + param_str3 + partner_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
            'target': 'new',
        }

    @api.multi
    def create_report_stock_picking_detail_export(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_stock_picking_detail.rptdesign"
        from_date = datetime.strptime(self.from_date, "%Y-%m-%d").date()
        to_date = datetime.strptime(self.to_date, "%Y-%m-%d").date()
        param_str1 = "&from_date=" + str(from_date) + "&to_date=" + str(to_date)
        param_str2 = "&product_ids="
        param_str3 = "&partner_ids="
        partner_id = '0'
        product_id = '0'
        if self.product_ids:
            if len(self.product_ids) > 10:
                raise UserError('Số lượng dịch vụ không vượt quá 10. Vui lòng kiểm tra lại!')
            product = ''
            for emp in self.product_ids:
                product += ',' + str(emp.id)
            product_id = (product[1:])
        if self.partner_ids:
            if len(self.partner_ids) > 10:
                raise UserError('Số lượng khách hàng không vượt quá 10 người. Vui lòng kiểm tra lại!')
            partner = ''
            for line in self.partner_ids:
                partner += ',' + str(line.id)
            partner_id = (partner[1:])
        param_str = param_str1 + param_str2 + product_id + param_str3 + partner_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }
