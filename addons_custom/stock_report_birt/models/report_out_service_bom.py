# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import ValidationError, UserError



class ReportOutServiceBom(models.TransientModel):
    _name = "report.out.service.bom"

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    partner_ids = fields.Many2many('res.partner', string='Partner')
    product_ids = fields.Many2many('product.product', string='Product', domain=[('type', '!=', 'service')])
    service_ids = fields.Many2many('product.product', string='Servicek', domain=[('type', '=', 'service')])
    employee_ids = fields.Many2many('hr.employee', string='Employee')

    @api.multi
    def create_report_out_service_bom(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_out_service_bom.rptdesign"
        from_date = datetime.strptime(self.from_date, "%Y-%m-%d").date()
        to_date = datetime.strptime(self.to_date, "%Y-%m-%d").date()
        param_str1 = "&from_date=" + str(from_date) + "&to_date=" + str(to_date)
        param_str2 = "&product_ids="
        param_str3 = "&partner_ids="
        param_str4 = "&service_ids="
        param_str5 = "&employee_ids="
        partner_id = '0'
        product_id = '0'
        service_id = '0'
        employee_id = '0'
        if self.product_ids:
            if len(self.product_ids) > 10:
                raise UserError('Số lượng nhân viên không vượt quá 10 người. Vui lòng kiểm tra lại!')
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
        if self.service_ids:
            if len(self.service_ids) > 10:
                raise UserError('Số lượng nhân viên không vượt quá 10 người. Vui lòng kiểm tra lại!')
            service = ''
            for ser in self.service_ids:
                service += ',' + str(ser.id)
            service_id = (service[1:])
        if self.employee_ids:
            if len(self.employee_ids) > 10:
                raise UserError('Số lượng dịch vụ không vượt quá 10. Vui lòng kiểm tra lại!')
            employee = ''
            for line in self.employee_ids:
                employee += ',' + str(line.id)
            employee_id = (employee[1:])
        param_str = param_str1 + param_str2 + product_id + param_str3 + partner_id + param_str4 + service_id + param_str5 + employee_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
            'target': 'new',
        }

    @api.multi
    def create_report_out_service_bom_export(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_out_service_bom.rptdesign"
        from_date = datetime.strptime(self.from_date, "%Y-%m-%d").date()
        to_date = datetime.strptime(self.to_date, "%Y-%m-%d").date()
        param_str1 = "&from_date=" + str(from_date) + "&to_date=" + str(to_date)
        param_str2 = "&product_ids="
        param_str3 = "&partner_ids="
        param_str4 = "&service_ids="
        param_str5 = "&employee_ids="
        partner_id = '0'
        product_id = '0'
        service_id = '0'
        employee_id = '0'
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
        if self.service_ids:
            if len(self.service_ids) > 10:
                raise UserError('Số lượng nhân viên không vượt quá 10 người. Vui lòng kiểm tra lại!')
            service = ''
            for ser in self.service_ids:
                service += ',' + str(ser.id)
            service_id = (service[1:])
        if self.employee_ids:
            if len(self.employee_ids) > 10:
                raise UserError('Số lượng dịch vụ không vượt quá 10. Vui lòng kiểm tra lại!')
            employee = ''
            for line in self.employee_ids:
                employee += ',' + str(line.id)
            employee_id = (employee[1:])
        param_str = param_str1 + param_str2 + product_id + param_str3 + partner_id + param_str4 + service_id + param_str5 + employee_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }
