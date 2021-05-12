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


class PartnerGift(models.Model):
    _name = 'partner.gift'

    name = fields.Char(string="Partner Gift")
    partner_id = fields.Many2one('res.partner', string="Partner")
    gift_id = fields.Many2one('stock.production.lot', string="Gift")
    gift_product_id = fields.Many2one('product.product', related='gift_id.product_id', store=True, readonly="True")
    gift_name = fields.Char(related='gift_product_id.name', string='Gift Name', readonly="True")
    gift_code = fields.Char(related="gift_id.name", readonly="True", store=True, string="Name gift")
    gift_status = fields.Selection(related='gift_id.x_status', string="Status gift", readonly="True")
    gift_expired_date = fields.Datetime(related='gift_id.life_date', string="Expired Date", readonly="True")
    content = fields.Text(string='Content')
    reason_gift_id = fields.Many2one('partner.gift.reason', string='Partner Gift Reason')
    pos_order_id = fields.Many2one('pos.order', string='Pos Order')

    @api.multi
    def action_cancel_gift(self):
        for gift in self:
            gift.gift_id.update({
                'x_status': 'destroy',
            })


class PartnerGiftReason(models.Model):
    _name = 'partner.gift.reason'

    name = fields.Char(string="Partner Gift Reason")
    partner_gift_ids = fields.One2many('partner.gift', 'reason_gift_id', string='Partner Gift')
    active = fields.Boolean(string='Active', default='True')