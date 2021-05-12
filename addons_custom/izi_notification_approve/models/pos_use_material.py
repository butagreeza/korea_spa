# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from odoo.exceptions import except_orm, ValidationError, UserError

class PosUsermaterial(models.Model):
    _inherit = 'pos.user.material'

    @api.multi
    def action_done(self):
        res = super(PosUsermaterial, self).action_done()
        res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'pos.user.material')]).id
        activity_ids = self.env['mail.activity'].sudo().search(
            [('res_model_id', '=', res_model_id), ('res_id', '=', self.id)])
        if len(activity_ids) > 0:
            activity_ids.sudo().action_done()
        return res
