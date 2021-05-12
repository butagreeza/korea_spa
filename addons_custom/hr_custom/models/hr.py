# -*- coding: utf-8 -*-
from odoo import fields, models, api
from . import utils
from odoo.exceptions import except_orm, Warning


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    x_employee_code = fields.Char(string="Employee Code")
    x_date_published = fields.Date(string="Date Published")
    x_street = fields.Text(string="Street")
    x_place_published = fields.Char(string="Place Published")
    x_tax_id = fields.Char(string="Tax Identification")
    x_work_service = fields.Boolean('Work Service', default=False)
    x_branch_id = fields.Many2one('res.branch', related='department_id.x_branch_id', readonly=True, store=True)

    _sql_constraints = [
        ('x_employee_code_uniq', 'unique(x_employee_code)', 'Employee Code is unique')
    ]

    @api.model
    def create(self, vals):
        if vals.get('x_employee_code') == False:
            code = utils.get_sequence(self._cr, 1, "NV1")
            while len(self.env['hr.employee'].search([('x_employee_code', '=', code)])) != 0:
                code = utils.get_sequence(self._cr, 1, "NV1")
            vals['x_employee_code'] = code
        else:
            if ' ' in vals.get('x_employee_code'):
                raise Warning("No spaces allowed in Code input")
            vals['x_employee_code'] = vals.get('x_employee_code').upper()
        return super(hr_employee, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'employee_code' in vals.keys():
            if vals.get('x_employee_code') == False:
                code = utils.get_sequence(self._cr, 1, "NV1")
                while len(self.env['hr.employee'].search([('x_employee_code', '=', code)])) != 0:
                    code = utils.get_sequence(self._cr, 1, "NV1")
                vals['x_employee_code'] = code
            else:
                if ' ' in vals.get('x_employee_code'):
                    raise Warning("No spaces allowed in Code input")
                vals['x_employee_code'] = vals.get('x_employee_code').upper()
        return super(hr_employee, self).write(vals)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            code = ''
            if record.department_id:
                if record.department_id.x_branch_id:
                    code = record.department_id.x_branch_id.code
            name = '%s[%s]' % (str(record.name), str(code and code or ''),)
            result.append((record.id, name))
        return result