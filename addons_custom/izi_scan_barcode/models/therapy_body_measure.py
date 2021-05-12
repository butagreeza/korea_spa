# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta

class TherapyBodyMeasure_(models.Model):
    _inherit = 'therapy.body.measure'

    # scan_bare_line = fields.Many2one('scan.barcode.izi.service.card.using.line')
    using_line_id = fields.Many2one('izi.service.card.using.line')


    @api.multi
    def action_confirm(self):

        # using_obj = self.env['izi.service.card.using'].search([('service_card1_ids', '=', self.using_line_id.id)])
        # # self.using_line_id.action_done()
        # therapy_prescription_id = self.env['therapy.prescription'].search([('izi_service_card_using_ids', '=', using_obj.id)])
        #
        # if therapy_prescription_id:
        #     therapy_record_id = self.env['therapy.record'].search([('therapy_prescription_id_ids', '=', therapy_prescription_id.id)])
        # print using_obj
        pass



    @api.multi
    def action_cancle(self):
        pass