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


class PartnerStageHistory(models.Model):
    _name = 'partner.stage.history'
    _description = 'Partner stage history'

    name = fields.Char(string="Name")
    partner_id = fields.Many2one('res.partner', string='Partner')
    time_change = fields.Datetime(string='Time change')
    from_stage_id = fields.Many2one('crm.stage', string='From stage')
    from_stage_name = fields.Char(string='From stage name')
    to_stage_id = fields.Many2one('crm.stage', string='To stage')
    to_stage_name = fields.Char(string='To stage name')
    user_id = fields.Many2one('res.users', string='User change')


class Partner(models.Model):
    _inherit = 'res.partner'

    x_stage_history_ids = fields.One2many('partner.stage.history', 'partner_id', string='Stage history')