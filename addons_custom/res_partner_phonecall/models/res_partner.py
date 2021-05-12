# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import except_orm, ValidationError, UserError
from odoo.osv import expression
from odoo import sys, os
import base64, time
from os.path import join
from datetime import datetime, date, timedelta
import logging, re
from odoo import http
from lxml import etree
from odoo.osv.orm import setup_modifiers
from dateutil.relativedelta import relativedelta
import requests
import json


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_phonecall_ids = fields.One2many("phonecall", "partner_id", string="Phone Calls")
    x_call_last_date = fields.Datetime(string='Call last date')

    @api.constrains('x_phonecall_ids')
    def onchange_phonecall(self):
        for partner in self:
            if partner.x_phonecall_ids:
                len_phone = len(partner.x_phonecall_ids) - 1
                partner.x_call_last_date = partner.x_phonecall_ids[0].start_time