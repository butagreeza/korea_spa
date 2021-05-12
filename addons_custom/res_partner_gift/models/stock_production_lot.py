# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('default_order_id'):
            arr_gift = []
            order_id = self.env['pos.order'].search([('id', '=', self._context.get('default_order_id'))])
            partner_gift_ids = self.env['partner.gift'].search([('partner_id', '=', order_id.partner_id.id)])
            for partner_gift_id in partner_gift_ids:
                arr_gift.append(partner_gift_id.gift_id.id)
            recs = self.search([('id', 'in', arr_gift), ('x_status', 'not in', ['destroy', 'used'])] + args,
                               limit=limit)
            return recs.name_get()
        if self._context.get('default_using_service_id'):
            arr_gift = []
            order_id = self.env['izi.service.card.using'].search([('id', '=', self._context.get('default_using_service_id'))])
            partner_gift_ids = self.env['partner.gift'].search([('partner_id', '=', order_id.customer_id.id)])
            for partner_gift_id in partner_gift_ids:
                arr_gift.append(partner_gift_id.gift_id.id)
            recs = self.search([('id', 'in', arr_gift), ('x_status', 'not in', ['destroy', 'used'])] + args,
                               limit=limit)
            return recs.name_get()


    def action_payment(self, order):
        amount_product = 0
        for product_id in self.product_id.x_product_card_ids:
            for order_line in order.lines:
                if product_id.id == order_line.product_id.id:
                    amount_product += order_line.price_subtotal_incl
        return amount_product