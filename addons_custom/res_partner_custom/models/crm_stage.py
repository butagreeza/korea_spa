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


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    x_day_number_remind = fields.Integer(string="Day number remind", default=0)
    x_code = fields.Char(string='Code')

    _sql_constraints = {
        ('unique_x_code', 'unique(x_code)', ' Mã phải là duy nhất!')
    }

    @api.model_cr
    def init(self):
        if not self.env['crm.stage'].search([('x_code', '=', 'call_now')], limit=1):
            self.env['crm.stage'].create({
                'name': _('Call now'),
                'x_code': 'call_now',
                'probability': 0
            })
        if not self.env['crm.stage'].search([('x_code', '=', 'lead')], limit=1):
            self.env['crm.stage'].create({
                'name': _('Lead'),
                'x_code': 'lead',
                'probability': 0
            })
        if not self.env['crm.stage'].search([('x_code', '=', 'reference')], limit=1):
            self.env['crm.stage'].create({
                'name': _('Reference'),
                'x_code': 'reference',
                'probability': 0
            })
        if not self.env['crm.stage'].search([('x_code', '=', 'reference2')], limit=1):
            self.env['crm.stage'].create({
                'name': _('Reference2'),
                'x_code': 'reference2',
                'probability': 0
            })
        if not self.env['crm.stage'].search([('x_code', '=', 'opportunity')], limit=1):
            self.env['crm.stage'].create({
                'name': _('Opportunity'),
                'x_code': 'opportunity',
                'probability': 0
            })
        if not self.env['crm.stage'].search([('x_code', '=', 'won')], limit=1):
            self.env['crm.stage'].create({
                'name': _('Won'),
                'x_code': 'won',
                'probability': 0
            })
        if not self.env['crm.stage'].search([('x_code', '=', 'lose')], limit=1):
            self.env['crm.stage'].create({
                'name': _('Lose'),
                'x_code': 'lose',
                'probability': 0
            })


class Partner(models.Model):
    _inherit = 'res.partner'

    def _default_stage_id(self):
        stage = self.env['crm.stage'].search([('x_code', '=', 'call_now')], limit=1)
        if not stage:
            self.env['crm.stage'].create({
                'name': _('Call now'),
                'x_code': 'call_now',
                'probability': 0
            })
        return stage.id

    x_stage_id = fields.Many2one('crm.stage', string='Stage', track_visibility='onchange', index=True,
                                 default=_default_stage_id)
    x_stage_code = fields.Char(related='x_stage_id.x_code', string="Stage code", readonly=True, store=True)