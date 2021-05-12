# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import except_orm, ValidationError
from datetime import datetime, timedelta, date as my_date
from dateutil.relativedelta import relativedelta


class MergeUseServiceGuarantee(models.Model):
    _name = 'merge.use.service.guarantee'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Code")
    service_id = fields.Many2one('product.product', "Service")
    max_use_count = fields.Float("Max Use Count")
    paid_count = fields.Float("Paid Count")
    used_count = fields.Float("Used Count")
    quantity = fields.Float("Quantity")
    uom_id = fields.Many2one('product.uom')
    employee_ids = fields.Many2many('hr.employee', string="Employee")
    merge_service_id = fields.Many2one('merge.use.service', "Merge Service", ondelete='cascade')
    price_unit = fields.Float("Price Unit", default=0)
    discount = fields.Float("Discount(%)")
    amount = fields.Float("Amount Total", compute="_compute_amount_total", store=True)
    # customer_rate = fields.Selection([(0, 'Normal'), (1, 'Good'), (2, "Excellent")], default=2)
    # customer_comment = fields.Text("Customer Comment")
    is_gift = fields.Boolean("Gift", default=False)
    # work_type = fields.Selection([('book', "Book"), ('tour', "Tour")], default='book')
    doctor_ids = fields.Many2many('hr.employee', string="Doctor")
    branch_id = fields.Many2one('res.branch', related="merge_service_id.pos_session_id.branch_id", string="Branch")
    # tiennq them nut bao hanh 06/08
    show_button = fields.Boolean('Visible', compute='_compute_show_button')
    guarantee_id = fields.Many2one('guarantee.line', "Guarantee")

    @api.depends('service_id')
    def _compute_show_button(self):
        for s in self:
            if s.service_id.x_guarantee == True:
                s.show_button = True
            else:
                s.show_button = False

    # @api.constrains('service_id')
    # def _check_service_id(self):
    #     for s in self:
    #         if s.service_id.x_type_service == 'spa' and s.service_id.type == 'service' and s.service_id.bom_service_count == 0:
    #             raise ValidationError('Dịch vụ [%s]%s có loại dịch vụ là %s bắt buộc phải cấu hình nguyên vật liệu!' % (str(s.service_id.default_code), str(s.service_id.name), str(s.service_id.x_type_service)))

    # @api.constrains('quantity')
    # def _check_quantity(self):
    #     for s in self:
    #         if s.quantity <= 0:
    #             raise ValidationError('Số lượng dịch vụ [%s]%s phải lớn hơn 0!' % (str(s.service_id.default_code), str(s.service_id.name)))


    # @api.onchange('employee_ids', 'service_id', 'quantity')
    # def onchange_employee(self):
    #     ids = []
    #     branch_ids = self.env['res.branch'].search([('brand_id', '=', self.using_id.pos_session_id.config_id.pos_branch_id.brand_id.id)])
    #     department_ids = self.env['hr.department'].search(
    #         [('x_branch_id', 'in', branch_ids.ids)])
    #     for line in department_ids:
    #         ids_o2m = self.env['hr.employee'].search([('department_id', '=', line.id), ('x_work_service', '=', True)])
    #         for id in ids_o2m:
    #             ids.append(id.id)
    #     return {
    #         'domain': {
    #             'employee_ids': [('id', 'in', ids)]
    #         }
    #     }

    @api.onchange('doctor_ids')
    def onchange_employee_tour(self):
        ids = []
        branch_ids = self.env['res.branch'].search(
            [('brand_id', '=', self.merge_service_id.pos_session_id.config_id.pos_branch_id.brand_id.id)])
        department_ids = self.env['hr.department'].search(
            [('x_branch_id', 'in', branch_ids.ids)])
        for line in department_ids:
            ids_o2m = self.env['hr.employee'].search([('department_id', '=', line.id), ('x_work_service', '=', True)])
            for id in ids_o2m:
                ids.append(id.id)
        return {
            'domain': {
                'doctor_ids': [('id', 'in', ids)]
            }
        }


    @api.onchange('service_id', 'quantity')
    def onchange_service(self):
        price = 0
        self.price_unit = price


    @api.onchange('service_id')
    def onchange_service_quantity(self):
        self.quantity = 1

    @api.onchange('quantity', 'price_unit')
    def onchange_quantity_price(self):
        self.amount = self.quantity * self.price_unit
        if self.quantity < 0:
            raise except_orm('Cảnh báo!', ("Số lượng phải lớn hơn không. Vui lòng kiểm tra lại"))


    @api.depends('quantity', 'price_unit','discount')
    def _compute_amount_total(self):
        for line in self:
            line.amount = line.quantity * line.price_unit * (1 - (line.discount/100))

    @api.onchange('service_id')
    def _onchange_izi_pos_product_id(self):
        list = []
        for item in self.merge_service_id.pos_session_id.config_id.x_category_ids:
            product_ids = self.env['product.product'].search(
                [('pos_categ_id', '=', item.id), ('active', '=', True), ('product_tmpl_id.type', '=', 'service')])
            for product_id in product_ids:
                list.append(product_id.id)
        return {
            'domain': {'service_id': [('id', 'in', list)]}
        }