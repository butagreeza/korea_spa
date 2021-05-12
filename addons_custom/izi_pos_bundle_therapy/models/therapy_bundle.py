# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError, MissingError
import time


class TherapyBundle(models.Model):
    _name = 'therapy.bundle'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Therapy bundle')
    amount_total = fields.Float(string='Amount total')
    order_id = fields.Many2one('pos.order', string='Order')
    partner_id = fields.Many2one('res.partner', related='therapy_record_id.partner_id', string="Partner", track_visibility='onchange', readonly=True)
    state = fields.Selection([('in_therapy', 'In Therapy'), ('signed_commitment', 'Signed Committed'), ('stop_care', 'Stop Care'), ('cancel', 'Cancel')], default="in_therapy", string='State')
    file_attach = fields.Binary(string='File Attach')
    therapy_bundle_line_ids = fields.One2many('therapy.bundle.line', 'therapy_bundle_id', string='Therapy bundle Line')
    therapy_record_id = fields.Many2one('therapy.record', string='Therapy Record')

    @api.model
    def create(self, vals):
        therapy_bundle = super(TherapyBundle, self).create(vals)
        if not therapy_bundle.name:
            offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
            hours = offset / 60 / 60 * -1
            date = datetime.strptime(therapy_bundle.create_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=hours)
            therapy_bundle.write({
                'name': 'GLT_%s_%s' % (str(therapy_bundle.partner_id.x_code), str(date))
            })
        return therapy_bundle

    def action_sign_therapy_bundle(self):
        self.state = 'signed_commitment'

    def action_stop_care(self):
        self.state = 'stop_care'

    def action_cancel(self):
        self.state = 'cancel'


class TherapyBundleLine(models.Model):
    _name = 'therapy.bundle.line'

    name = fields.Char('Therapy bundle')
    product_id = fields.Many2one('product.product', string='Product')
    uom_id = fields.Many2one('product.uom', string='Unit of  Measure')
    qty = fields.Integer(string='Quantity')
    body_area_ids = fields.Many2many('body.area', string="Body area")
    therapy_bundle_id = fields.Many2one('therapy.bundle', string='Therapy bundle')