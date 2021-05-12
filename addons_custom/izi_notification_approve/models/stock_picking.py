# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Tắt thông báo khi đã xác nhận xuất kho
    @api.multi
    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'button_validate')]).id
        activity_ids = self.env['mail.activity'].sudo().search(
            [('res_model_id', '=', res_model_id), ('res_id', '=', self.id)])
        if len(activity_ids) > 0:
            activity_ids.sudo().action_done()
        return res


    def schedule_activity_inventory(self, summary, user_id, to_date, sid):
        res_model_id = self.env['ir.model'].search([('model', '=', 'stock.picking')]).id
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
