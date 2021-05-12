# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PosPaymentWithCoin(models.Model):
    _name = 'pos.payment.with.service'

    product_ids = fields.Many2many('product.product', string="Product")
    journal_id = fields.Many2one('account.journal')




class AccountJournal(models.Model):
    _name = 'account.journal'

    pos_payment_id = fields.One2many('pos.payment.with.service', 'journal_id', "Pos Payment")

