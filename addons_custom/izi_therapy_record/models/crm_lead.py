# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, http
from odoo.exceptions import except_orm, UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.multi
    def action_open_therapy_record(self):
        action = self.env.ref('izi_therapy_record.action_izi_therapy_record').read()[0]
        therapy_records = self.env['therapy.record'].search([('partner_id', '=', self.partner_id.id)])
        if len(therapy_records) > 1:
            action['domain'] = [('id', 'in', therapy_records.ids)]
            action['context'] = {'default_partner_id': self.partner_id.id}
        elif therapy_records:
            action['views'] = [(self.env.ref('izi_therapy_record.izi_view_therapy_record_form').id, 'form')]
            action['res_id'] = therapy_records.id
            action['context'] = {'default_partner_id': self.partner_id.id}
        else:
            action['context'] = {'default_partner_id': self.partner_id.id}
            action['domain'] = [('id', '=', 0)]
        return action