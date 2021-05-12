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


class PartnerStatus(models.Model):
    _name = 'partner.status'

    name = fields.Char(string="Name")
    description = fields.Char(string="Description")


class Partner(models.Model):
    _inherit = 'res.partner'

    x_partner_status_ids = fields.Many2many('partner.status', string="Partner status", track_visibility='onchange')
