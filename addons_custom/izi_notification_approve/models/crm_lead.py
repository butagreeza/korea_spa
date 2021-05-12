# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def create(self, vals):
        res = super(CrmLead, self).create(vals)
        # if res.team_id:
        #     res.schedule_activity('Lead', res.team_id.user_id.id, res.create_date, res.id)
        # if res.user_id:
        #     res.schedule_activity('Lead', res.user_id.id, res.create_date, res.id)
        return res

    @api.multi
    def write(self, vals):
        # if vals.get('user_id'):
            # self.schedule_activity('Lead', vals.get('user_id'), self.create_date, self.id)
        return super(CrmLead, self).write(vals)


    @api.multi
    def action_set_won(self):
        res = super(CrmLead, self).action_set_won()
        res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'crm.lead')]).id
        activity_ids = self.env['mail.activity'].sudo().search(
            [('res_model_id', '=', res_model_id), ('res_id', '=', self.id)])
        if len(activity_ids) > 0:
            activity_ids.sudo().action_done()
        return res

    @api.multi
    def action_set_lost(self):
        res = super(CrmLead, self).action_set_lost()
        res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'crm.lead')]).id
        activity_ids = self.env['mail.activity'].sudo().search(
            [('res_model_id', '=', res_model_id), ('res_id', '=', self.id)])
        if len(activity_ids) > 0:
            activity_ids.sudo().action_done()
        return res

    @api.multi
    def action_quotes(self):
        res = super(CrmLead, self).action_quotes()
        res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'crm.lead')]).id
        activity_ids = self.env['mail.activity'].sudo().search(
            [('res_model_id', '=', res_model_id), ('res_id', '=', self.id)])
        if len(activity_ids) > 0:
            activity_ids.sudo().action_done()
        return res

    def schedule_activity(self, summary, user_id, to_date, sid):
        res_model_id = self.env['ir.model'].search([('model', '=', 'crm.team')]).id
        argvs = {
            'activity_type_id': 2,
            'user_id': user_id or 1,
            'date_deadline': to_date,
            'recommended_activity_type_id': False,
            'previous_activity_type_id': False,
            'summary': summary,
            'note': ' ',
            'res_model_id': res_model_id,
            'activity_category': 'default',
            'res_id': sid
        }
        self.env['mail.activity'].create(argvs)