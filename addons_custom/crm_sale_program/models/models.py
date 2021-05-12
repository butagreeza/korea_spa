# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, RedirectWarning, except_orm
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import mute_logger
import logging


class crm_sale_program(models.Model):
    _name = 'crm.sale.program'

    name = fields.Char(string='Name', required=True)
    type = fields.Selection([('birthday', 'Birthday'), ('new_customer', 'New Customer'),
                             ('vip', 'Vip'), ('product', 'Product')],
                            default='')
    description = fields.Text(string='Description', required=True)
    line_ids = fields.One2many('crm.sale.program.line', 'program_id')
    from_date = fields.Date(string='From date')
    to_date = fields.Date(string='To date')

    @api.onchange('line_ids')
    def onchange_line_ids(self):
        for index1 in range(len(self.line_ids)):
            # print  index1
            for index2 in range(len(self.line_ids)):
                if index1 != index2:
                    if self.line_ids[index1].partner_id.id == self.line_ids[index2].partner_id.id:
                        raise except_orm('Thông báo', 'Khách hàng không được trùng nhau')


class crm_sale_program_line(models.Model):
    _name = 'crm.sale.program.line'

    program_id = fields.Many2one('crm.sale.program')
    partner_id = fields.Many2one('res.partner', string='Partner')
    x_birthday = fields.Date(string = "Birth Day", related='partner_id.x_birthday')
    x_rank = fields.Many2one('crm.vip.rank', string='Rank', related='partner_id.x_rank')


class CrmPartnerLine(models.TransientModel):
    _name = "crm.sale.program.partner.line"

    program_rel_id = fields.Many2one('crm.sale.program.partner', "Relation")
    partner_id = fields.Many2one('res.partner', string="Partner")
