# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResBranch(models.Model):
    _name = 'res.branch'
    _description = 'Branch'

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True)
    telephone = fields.Char(string='Telephone No')
    address = fields.Text('Address')
    code = fields.Char("Code")
    brand_id = fields.Many2one('res.brand', string="Brand")

    partner_sequence_id = fields.Many2one('ir.sequence', string='Partner Sequence', readonly=True,
        help="Đây là mẫu trình tự sinh mã khách hàng cho nhóm bán hàng của chi nhánh.", copy=False)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Code is unique'),
    ]

    @api.constrains('code')
    def _constrain_code(self):
        if self.code and self.partner_sequence_id:
            self.partner_sequence_id.write({
                'prefix': "%s" % self.code,
                'code': "%s_partner_code" % self.code,
            })

    @api.model
    def create(self, vals):
        vals['partner_sequence_id'] = self.create_partner_sequence(vals['name'], vals['code'], vals.get('company_id', False))
        if vals.get('code'):
            vals['code'] = vals['code'].upper()
        else:
            raise UserError("Vui lòng cấu mã chi nhánh ở điểm bán hàng  !")
        return super(ResBranch, self).create(vals)

    @api.multi
    def action_create_partner_sequence(self):
        if self.partner_sequence_id: raise UserError('Chi nhánh đã có trình sinh mã khách hàng, không thể tạo mới!')
        self.write({
            'partner_sequence_id': self.create_partner_sequence(self.name, self.code, self.company_id.id)
        })

    def create_partner_sequence(self, branch_name, branch_code, company):
        IrSequence = self.env['ir.sequence'].sudo()
        val = {
            'name': _('Partner code %s') % branch_name,
            'padding': 1,
            'prefix': "%s" % branch_code,
            'code': "%s_partner_code" % branch_code,
            'company_id': company,
        }
        return IrSequence.create(val).id