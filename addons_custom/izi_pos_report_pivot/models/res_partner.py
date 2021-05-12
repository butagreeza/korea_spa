# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, RedirectWarning, except_orm, UserError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import mute_logger
import logging

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        partner_ids = super(ResPartner, self).name_search(name, args, operator, limit)
        if self._context.get('user_ids'):
            domain = []
            if name:
                domain = [('display_name', 'ilike', name),]
            if self._context.get('user_ids')[0][2]:
                domain += [('user_id', 'in', self._context.get('user_ids')[0][2])]
            partner_ids = self.env['res.partner'].search(domain).name_get()
        return partner_ids