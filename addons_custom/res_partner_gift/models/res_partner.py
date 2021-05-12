# -*- coding: utf-8 -*-
from odoo import models, api, fields , _
from odoo.exceptions import except_orm, ValidationError
from odoo.osv import expression
from odoo import sys, os
import base64, time
from os.path import  join
from datetime import datetime,date
import logging, re
from odoo import http
from odoo.osv.orm import setup_modifiers
from dateutil.relativedelta import relativedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_gift_ids = fields.One2many('partner.gift', 'partner_id', string="Parter Gift")

    @api.multi
    def action_give(self):
        for partner in self:
            ctx = self.env.context.copy()
            ctx.update({
                'default_partner_id': partner.id,
                'default_pricelist_id': partner.property_product_pricelist.id
            })
            view = self.env.ref('res_partner_gift.pos_order_gift_form_view')
            return {
                'name': 'Give present',
                'type': 'ir.actions.act_window',
                'res_model': 'pos.order',
                'view_mode': 'form',
                'view_type': 'form',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'current',
                'res_id': False,
                'context': ctx
            }

    @api.multi
    def action_cancel_gift(self):
        for gift in self:
            pass
