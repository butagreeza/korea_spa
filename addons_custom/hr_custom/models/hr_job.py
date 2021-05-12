# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm

class HrJob(models.Model):
    _inherit = 'hr.job'

    x_code = fields.Char('Code',required=1)

    @api.model
    def create(self, vals):
        if vals.get("x_code") != None:
            if len(self.env['hr.job'].search([('x_code', '=', vals.get("x_code").upper())])) != 0:
                raise  except_orm('Cảnh báo!', ("The code you entered already exists"))
            if ' ' in vals.get('x_code'):
                raise  except_orm('Cảnh báo!', ("No spaces allowed in Code input"))
            vals['x_code'] = vals.get('x_code').upper()
        return super(HrJob,self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get("x_code") != None:
            if len(self.env['hr.job'].search(
                    [('x_code', '=', vals.get("x_code").upper())])) != 0:
                raise except_orm('Cảnh báo!', ("The code you entered already exists"))
            if ' ' in vals.get('x_code'):
                raise except_orm('Cảnh báo!', ("No spaces allowed in Code input"))
            vals['x_code'] = vals.get('x_code').upper()
        return super(HrJob, self).write(vals)



