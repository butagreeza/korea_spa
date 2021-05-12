# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PartnerInteractionMeeting(models.TransientModel):
    _name = 'partner.interaction.meeting'

    time_from = fields.Datetime(string="Time from")
    team_id = fields.Many2one('crm.team', string="Team")
    product_ids = fields.Many2many('product.product', string="Products")
    partner_id = fields.Many2one('res.partner', string='Partner')
    description = fields.Text(string='Description')
    user_id = fields.Many2one('res.users', string='User')

    @api.multi
    def action_confirm(self):
        for s in self:
            stage_id = self.env['crm.stage'].search([('x_code', '=', 'meeting')], limit=1)
            if not stage_id:
                stage_id = self.env['crm.stage'].create({
                    'name': _('Meeting'),
                    'x_code': 'meeting',
                    'probability': 0
                })
            lead = self.env['crm.lead'].create({
                'name': s.partner_id.name,
                'partner_id': s.partner_id.id,
                'partner_name': s.partner_id.name,
                'phone': s.partner_id.phone,
                'x_birthday': s.partner_id.x_birthday,
                'email_from': s.partner_id.email,
                'description': s.description,
                'street': s.partner_id.street,
                'team_id': s.team_id.id,
                'stage_id': stage_id.id,
            })
            self.env['service.booking'].create({
                'customer_id': s.partner_id.id,
                'time_from': s.time_from,
                'lead_id': lead.id,
                'services': [(6, 0, s.product_ids.ids)]
            })