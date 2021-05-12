# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import timedelta, datetime, date
from odoo.exceptions import ValidationError, except_orm, UserError


class ActivityHistory(models.TransientModel):
    _inherit = 'activity.history.assign'

    def confirm_transfer(self):
        check = False
        user = self.env['res.users'].search([('id', '=', self._uid)])
        if user.has_group('izi_res_permissions.group_leader_customer_care') or user.has_group(
                        'izi_res_permissions.group_leader_consultant'):
            check = True
        if self.activity_history_id:
            if self.activity_history_id.user_id:
                if self.activity_history_id.user_id.id != user.id and not check:
                    raise UserError(
                        'Nhân viên %s không có quyền chuyển lịch! Vui lòng liên lạc với quản lý để được xử lý' % (
                            user.name))
                else:
                    self.activity_history_id.update({
                        'state': 'move_remind',
                        'schedule_transfer_reason_id': self.schedule_transfer_reason_id.id,
                        'date_move_remind': self.date_move_remind,
                        'user_transfer': user.id,
                    })
                    mail_activity = self.env['mail.activity'].search(
                        [('res_id', '=', self.id), ('user_id', '=', self.user_id.id)], limit=1)
                    if mail_activity: mail_activity.unlink()
                    self.env['mail.activity'].create({
                        'activity_type_id': self.activity_history_id.mail_activity_type_id.id,
                        'res_model_id': self.env.ref('izi_crm_interaction.model_activity_history').id,
                        'res_model': self.env.ref('izi_crm_interaction.model_activity_history').name,
                        'res_id': self.activity_history_id.id,
                        'user_id': self.activity_history_id.user_id.id,
                        'date_deadline': self.date_move_remind,
                    })
            else:
                if not check:
                    raise UserError(
                        'Nhân viên %s không có quyền chuyển lịch! Vui lòng liên lạc với quản lý để được xử lý' % (
                            user.name))
                self.activity_history_id.update({
                    'state': 'move_remind',
                    'schedule_transfer_reason_id': self.schedule_transfer_reason_id.id,
                    'date_move_remind': self.date_move_remind,
                    'user_transfer': user.id,
                })

    def confirm_transfer_multi(self):
        check = False
        user = self.env['res.users'].search([('id', '=', self._uid)])
        if user.has_group('izi_res_permissions.group_leader_customer_care') or user.has_group(
                'izi_res_permissions.group_leader_consultant'):
            check = True
        activity_ids = self.env['activity.history'].search([('id', 'in', self._context.get('active_ids'))])
        if len(activity_ids) != len(activity_ids.filtered(lambda act:act.state not in ['interacted', 'cancel'])):
            raise UserError("Bạn đang giao việc cho lịch nhắc ở trạng thái đã có tương tác hoặc hủy. Vui lòng kiểm tra lại!")
        for activity_id in activity_ids:
            if activity_id.user_id:
                if activity_id.user_id.id != user.id and not check:
                    raise UserError(
                        'Nhân viên %s không có quyền chuyển lịch! Vui lòng liên lạc với quản lý để được xử lý' % (
                            user.name))
                else:
                    activity_id.write({
                        'state': 'move_remind',
                        'schedule_transfer_reason_id': self.schedule_transfer_reason_id.id,
                        'date_move_remind': self.date_move_remind,
                        'user_transfer': user.id,
                    })
                    mail_activity = self.env['mail.activity'].search(
                        [('res_id', '=', activity_id.id), ('user_id', '=', activity_id.user_id.id)], limit=1)
                    if mail_activity: mail_activity.unlink()
                    if activity_id.user_id:
                        self.env['mail.activity'].create({
                            'activity_type_id': activity_id.mail_activity_type_id.id,
                            'res_model_id': self.env.ref('izi_crm_interaction.model_activity_history').id,
                            'res_model': self.env.ref('izi_crm_interaction.model_activity_history').name,
                            'res_id': activity_id.id,
                            'user_id': activity_id.user_id.id,
                            'date_deadline': self.date_move_remind,
                        })
            else:
                if not check:
                    raise UserError(
                        'Nhân viên %s không có quyền chuyển lịch! Vui lòng liên lạc với quản lý để được xử lý' % (
                            user.name))
                activity_id.update({
                    'state': 'move_remind',
                    'schedule_transfer_reason_id': self.schedule_transfer_reason_id.id,
                    'date_move_remind': self.date_move_remind,
                    'user_transfer': user.id,
                })