# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import UserError, ValidationError, MissingError
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    therapy_prescription_return_product_line_ids = fields.One2many('therapy.prescription.return.product.line', 'partner_id', string='Return Product')
    therapy_record_count = fields.Integer(string='Therapy Record', compute='get_count_therapy_record')
    therapy_prescription_count = fields.Integer(string='Therapy Prescription', compute='get_count_therapy_record')

    # @api.depends('therapy_record_count', 'therapy_prescription_count')
    @api.multi
    def get_count_therapy_record(self):
        for line in self:
            therapy_record_ids = self.env['therapy.record'].search([('partner_id', '=', line.id)])
            if therapy_record_ids:
                line.therapy_record_count = len(therapy_record_ids)
            therapy_prescription_ids = self.env['therapy.prescription'].search([('partner_id', '=', line.id)])
            if therapy_prescription_ids:
                line.therapy_prescription_count = len(therapy_prescription_ids)