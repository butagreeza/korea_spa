# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import except_orm, ValidationError, UserError
from odoo.osv import expression
from odoo import sys, os
import base64, time
from os.path import join
from datetime import datetime, date


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        pass