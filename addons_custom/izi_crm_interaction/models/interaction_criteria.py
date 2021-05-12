# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import timedelta, datetime, date
from odoo.exceptions import ValidationError, except_orm, UserError


class InteractionFeedback(models.Model):
    _name = 'interaction.feedback'
    _description = 'Interaction Feedback'

    criteria_id = fields.Many2one('interaction.criteria', string='Criteria')
    option_id = fields.Many2one('interaction.criteria.option',string='Option')
    interaction_id = fields.Many2one('partner.interaction', string='Interaction')


class InteractionCriteria(models.Model):
    _name = 'interaction.criteria'
    _description = 'Interaction Criteria'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name')
    option_ids = fields.One2many('interaction.criteria.option', 'criteria_id', string='Option')


class InteractionCriteriaOption(models.Model):
    _name = 'interaction.criteria.option'
    _description = 'Interaction Criteria Option'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name')
    criteria_id = fields.Many2one('interaction.criteria', string='Criteria')
