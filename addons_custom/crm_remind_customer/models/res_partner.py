# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    service_calender_remider_ids = fields.One2many('crm.service.calender.reminder.line', 'partner_id', "Calender Reminder")