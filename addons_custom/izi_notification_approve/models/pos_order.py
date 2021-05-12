# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PosOrderNotification(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def action_send_payment(self):
        res = super(PosOrderNotification, self).action_send_payment()
        if self.state == 'to_approve':
            users = self.env['res.users'].search([
                ('groups_id', 'in', self.env.ref('izi_res_permissions.group_leader_shop').id),
                ('id', '!=', self._uid)])
            for line in users:
                if line.x_pos_config_id.id == self.session_id.config_id.id:
                    self.schedule_activity('Đơn hàng', line.id, self.date_order, self.id)
                if not line.x_pos_config_id:
                    self.schedule_activity('Đơn hàng', line.id, self.date_order, self.id)
        return res

    @api.multi
    def action_debt_approve(self):
        res = super(PosOrderNotification, self).action_debt_approve()
        res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'pos.order')]).id
        activity_ids = self.env['mail.activity'].sudo().search(
            [('res_model_id', '=', res_model_id), ('res_id', '=', self.id)])
        if len(activity_ids) > 0:
            activity_ids.sudo().action_done()
        users = self.env['res.users'].search([
            ('groups_id', 'in', self.env.ref('izi_res_permissions.group_cashier').id),
            ('id', '!=', self._uid)])
        for line in users:
            if line.x_pos_config_id.id == self.session_id.config_id.id:
                self.schedule_activity('Đơn hàng', line.id, self.date_order, self.id)
        self.schedule_activity('Đơn hàng', self._uid, self.date_order, self.id)
        return res

    @api.multi
    def action_order_confirm(self):
        res = super(PosOrderNotification, self).action_order_confirm()
        res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'pos.order')]).id
        activity_ids = self.env['mail.activity'].sudo().search(
            [('res_model_id', '=', res_model_id), ('res_id', '=', self.id)])
        if len(activity_ids) > 0:
            activity_ids.sudo().action_done()
        # chuyển thông báo xuống cho bộ phận kho
        users = self.env['res.users'].search([
            ('groups_id', 'in', self.env.ref('izi_res_permissions.group_inventory_accounting').id),
            ('id', '!=', self._uid)])
        for line in users:
            if line.x_pos_config_id.id == self.session_id.config_id.id:
                for x in self.picking_id:
                    if x.state != 'szzzcc':
                        x.schedule_activity_inventory('Xuất kho bán', line.id, self.date_order, x.id)
        return res

    @api.multi
    def action_order_cancel(self):
        res = super(PosOrderNotification, self).action_order_cancel()
        res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'pos.order')]).id
        activity_ids = self.env['mail.activity'].sudo().search(
            [('res_model_id', '=', res_model_id), ('res_id', '=', self.id)])
        if len(activity_ids) > 0:
            activity_ids.sudo().action_done()
        return res

    @api.multi
    def send_refund(self):
        res = super(PosOrderNotification, self).send_refund()
        users = self.env['res.users'].search([
            ('groups_id', 'in', self.env.ref('izi_res_permissions.group_leader_shop').id),
            ('id', '!=', self._uid)])
        for line in users:
            if line.x_pos_config_id.id == self.session_id.config_id.id:
                self.schedule_activity('Đơn hàng', line.id, self.date_order, self.id)
        self.schedule_activity('Đơn hàng', self._uid, self.date_order, self.id)
        return res

    @api.multi
    def action_cancel_refund(self):
        res = super(PosOrderNotification, self).action_cancel_refund()
        res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'pos.order')]).id
        activity_ids = self.env['mail.activity'].sudo().search(
            [('res_model_id', '=', res_model_id), ('res_id', '=', self.id)])
        if len(activity_ids) > 0:
            activity_ids.sudo().action_done()
        return res

    @api.multi
    def confirm_refund(self):
        res = super(PosOrderNotification, self).confirm_refund()
        res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'pos.order')]).id
        activity_ids = self.env['mail.activity'].sudo().search(
            [('res_model_id', '=', res_model_id), ('res_id', '=', self.id)])
        if len(activity_ids) > 0:
            activity_ids.sudo().action_done()
        return res

    def schedule_activity(self, summary, user_id, to_date, sid):
        res_model_id = self.env['ir.model'].search([('model', '=', 'pos.order')]).id
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


    # def schedule_activity_inventory(self, summary, user_id, to_date, sid):
    #     res_model_id = self.env['ir.model'].search([('model', '=', 'stock.picking')]).id
    #     argvs = {
    #         'activity_type_id': 2,
    #         'user_id': user_id or 1,
    #         'date_deadline': to_date,
    #         'recommended_activity_type_id': False,
    #         'previous_activity_type_id': False,
    #         'summary': summary,
    #         'note': ' ',
    #         'res_model_id': res_model_id,
    #         'activity_category': 'default',
    #         'res_id': sid
    #     }
    #     self.env['mail.activity'].create(argvs)