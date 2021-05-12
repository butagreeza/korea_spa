# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, except_orm, UserError
from datetime import datetime


class Partner(models.Model):
    _inherit = 'res.partner'

    x_interaction_ids = fields.One2many('partner.interaction', 'partner_id', string='Interaction')
    x_activity_ids = fields.One2many('activity.history', 'partner_id', string='Activity History')
    x_activity_count = fields.Integer(string='Count activity', compute='_compute_activity_count')
    x_interaction_count = fields.Integer(string='Count interaction', compute='_compute_interaction_count')
    x_special_caregiver = fields.Many2one('res.users', string='Special Caregiver', track_visibility='onchange')

    @api.multi
    def action_view_interaction(self):
        action = self.env.ref('izi_crm_interaction.partner_interaction_action_window').read()[0]
        interactions = self.mapped('x_interaction_ids')
        if len(interactions) > 1:
            action['domain'] = [('id', 'in', self.x_interaction_ids.ids)]
        elif interactions:
            action['views'] = [(self.env.ref('izi_crm_interaction.partner_interaction_form_view').id, 'form')]
            action['res_id'] = interactions.id
        else:
            action['domain'] = [('id', '=', 0)]
        self._table = 'partner_interaction'
        return action

    @api.depends('x_interaction_ids')
    def _compute_interaction_count(self):
        for s in self:
            s.x_interaction_count = len(s.x_interaction_ids)

    @api.multi
    def action_view_activity_history(self):
        action = self.env.ref('izi_crm_interaction.activity_history_action_window').read()[0]
        activity_ids = self.mapped('x_activity_ids')
        if len(activity_ids) > 1:
            action['domain'] = [('id', 'in', activity_ids.ids)]
        elif activity_ids:
            action['views'] = [(self.env.ref('izi_crm_interaction.activity_history_form_view').id, 'form')]
            action['res_id'] = activity_ids.id
        else:
            action['domain'] = [('id', '=', 0)]
        return action


    @api.depends('x_activity_ids')
    def _compute_activity_count(self):
        for s in self:
            s.x_activity_count = len(s.x_activity_ids)