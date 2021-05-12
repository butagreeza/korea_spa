# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm, UserError


class ReportWageServiceEmployee(models.TransientModel):
    _name = 'report.wage.service.employee'

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    employee_ids = fields.Many2many('hr.employee', string='Employee')
    partner_ids = fields.Many2many('res.partner', string='Partner')
    categ_ids = fields.Many2many('product.category', string='Category')
    type_service = fields.Selection([('card', 'Card'), ('service', 'Service'), ('bundle', 'Bundle'), ('guarantee', 'Guarantee'), ('guarantee_bundle', 'Guarantee Bundle')], string="Type")

    @api.multi
    def create_report_wage_service_to_employee(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_wage_service_to_employee.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str2 = "&employee_ids="
        param_str3 = "&partner_ids="
        param_str4 = "&categ_ids="
        param_str5 = "&type="
        partner_id = '0'
        categ_id = '0'
        employee_id = '0'
        type_service = '0'
        if self.employee_ids:
            if len(self.employee_ids) > 10:
                raise UserError('Số lượng nhân viên không vượt quá 10 người. Vui lòng kiểm tra lại!')
            employee = ''
            for emp in self.employee_ids:
                employee += ',' + str(emp.id)
            employee_id = (employee[1:])
        if self.partner_ids:
            if len(self.partner_ids) > 10:
                raise UserError('Số lượng khách hàng không vượt quá 10 người. Vui lòng kiểm tra lại!')
            partner = ''
            for line in self.partner_ids:
                partner += ',' + str(line.id)
            partner_id = (partner[1:])
        if self.categ_ids:
            if len(self.categ_ids) > 10:
                raise UserError('Số lượng nhóm dịch vụ không vượt quá 10 nhóm. Vui lòng kiểm tra lại!')
            categ = ''
            for line in self.categ_ids:
                categ += ',' + str(line.id)
            categ_id = (categ[1:])
            # for line in self.env['product.product'].search([('')]):
            #     service += ',' + str(line.id)
            # service_id = (service[1:])\
        if self.type_service:
            type_service = self.type_service
        param_str = param_str1 + param_str2 + employee_id + param_str3 + partner_id + param_str4 + categ_id + param_str5 + type_service
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
            'target': 'new',
        }

    @api.multi
    def create_report_wage_service_to_employee_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_wage_service_to_employee.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str2 = "&employee_ids="
        param_str3 = "&partner_ids="
        param_str4 = "&categ_ids="
        param_str5 = "&type="
        partner_id = '0'
        categ_id = '0'
        employee_id = '0'
        type_service = '0'
        if self.employee_ids:
            if len(self.employee_ids) > 10:
                raise UserError('Số lượng nhân viên không vượt quá 10 người. Vui lòng kiểm tra lại!')
            employee = ''
            for emp in self.employee_ids:
                employee += ',' + str(emp.id)
            employee_id = (employee[1:])
        if self.partner_ids:
            if len(self.partner_ids) > 10:
                raise UserError('Số lượng khách hàng không vượt quá 10 người. Vui lòng kiểm tra lại!')
            partner = ''
            for line in self.partner_ids:
                partner += ',' + str(line.id)
            partner_id = (partner[1:])
        if self.categ_ids:
            if len(self.categ_ids) > 10:
                raise UserError('Số lượng nhóm dịch vụ không vượt quá 10 nhóm. Vui lòng kiểm tra lại!')
            categ = ''
            for line in self.categ_ids:
                categ += ',' + str(line.id)
            categ_id = (categ[1:])
        if self.type_service:
            type_service = self.type_service
        param_str = param_str1 + param_str2 + employee_id + param_str3 + partner_id + param_str4 + categ_id + param_str5 + type_service
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }