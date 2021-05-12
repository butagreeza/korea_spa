# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import timedelta, datetime, date
from odoo.exceptions import ValidationError, except_orm, UserError

import logging

_logger = logging.getLogger(__name__)

class TherapyRecord(models.Model):
    _inherit = 'therapy.record'

    interaction_last_date = fields.Date(string='Interaction Last Date', track_visibility='onchange')
    out_of_medicine_date = fields.Date(string='Out of Medicine Date', track_visibility='onchange')
    first_medicine_date = fields.Date(string='First Medicine Date')
    interaction_ids = fields.Many2many('partner.interaction', string='Interactions')

    #todo nhắc lịch tự động cho chăm sóc khách hàng
    @api.model
    def cron_create_activity_history_auto(self):
        therapy_records = self.search([('state', 'in', ['in_therapy', 'signed_commitment']), ('categ_id.x_product_categ_remind_ids', '!=', False)])
        if therapy_records:
            is_activity_constant = False
            self.create_activity_history(therapy_records.ids, is_activity_constant)

    #todo hàm tạo lịch nhắc
    def create_activity_history(self, therapy_record_ids, is_activity_constant):
        for therapy_record_id in therapy_record_ids:
            therapy_record = self.search([('id', '=', therapy_record_id),], limit=1)
            if not therapy_record: raise UserError('Không tìm thấy hồ sơ trị liệu có id: %s! Liên hệ Admin để được giải quyết.' % (str(therapy_record_id)))
            if not therapy_record.categ_id.x_product_categ_remind_ids:
                raise UserError(
                    _("Nhóm dịch vụ %s chưa cấu hình nhắc lịch") % str(therapy_record.categ_id.name))
            config_remind = therapy_record.env['product.product'].get_config_remind(therapy_record.categ_id.x_product_categ_remind_ids)
            #nếu tạo lịch nhắc sau khi tạo tương tác muộn thì quét hết các lịch nhắc
            if is_activity_constant:
                reminds_created = therapy_record.env['activity.history'].search(
                    [('therapy_record_id', '=', therapy_record.id), ('state', 'not in', ['interacted', 'move_remind', 'cancel']), ('type', '=', 'customer_care')])
            #nếu tạo lịch tự động bằng job thì chỉ quét các lịch nhắc dc sinh tự động
            else:
                reminds_created = therapy_record.env['activity.history'].search(
                    [('therapy_record_id', '=', therapy_record.id), ('object', 'in', ['customer_care', 'special_caregiver']),
                     ('state', 'not in', ['interacted', 'move_remind', 'cancel']),
                     ('type', '=', 'customer_care'), ('is_activity_constant', '=', False)])
            # if reminds_created:
            #     for remind_created in reminds_created:
            #         remind_created.unlink()
            for config in config_remind:
                if config['repeat'] and therapy_record.interaction_last_date:
                    condition_end = timedelta(days=config['period']) + datetime.strptime(therapy_record.interaction_last_date, '%Y-%m-%d')
                    date_deadline = timedelta(days=config['date_number']) + datetime.strptime(therapy_record.interaction_last_date, '%Y-%m-%d')
                    while date_deadline < condition_end:
                        activity_history_id = self.env['activity.history'].search([('therapy_record_id', '=', therapy_record.id),
                                                                                   ('object', 'in', ['customer_care',
                                                                                                     'special_caregiver']),
                                                                                   ('type', '=', 'customer_care'),
                                                                                   ('date_move_remind', '=', date_deadline),
                                                                                   ('state', 'not in', ['cancel', 'interacted'])])
                        activity_history_created = therapy_record.env['activity.history'].search(
                            [('therapy_record_id', '=', therapy_record.id),
                             ('object', 'in', ['customer_care', 'special_caregiver']),
                             ('state', 'not in', ['interacted', 'cancel']),
                             ('date_deadline', '=', date_deadline),
                             ('type', '=', 'customer_care'), ('is_activity_constant', '=', False)])
                        if activity_history_id or activity_history_created:
                            pass
                        else:
                            remind = therapy_record.env['activity.history'].create({
                                'therapy_record_id': therapy_record.id,
                                'partner_id': therapy_record.partner_id.id,
                                'mail_activity_type_id': config['activity_type_id'],
                                'type': 'customer_care',
                                'object': 'special_caregiver' if therapy_record.partner_id.x_special_caregiver else config['object'],
                                'user_id': therapy_record.partner_id.x_special_caregiver.id if therapy_record.partner_id.x_special_caregiver else False,
                                'date_deadline': date_deadline,
                                'note': config['note']
                            })
                            if remind.user_id:
                                remind.action_assign()
                        date_deadline += timedelta(days=config['date_number'])

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        res = super(TherapyRecord, self).name_search()
        if self._context.get('partner_id'):
            therapy_record_ids = self.search([('partner_id', '=', self._context.get('partner_id'))])
            if self._context.get('search_activity'):
                therapy_record_ids = self.search([('state', 'in', ['in_therapy', 'signed_commitment']), ('partner_id', '=', self._context.get('partner_id'))])
            return therapy_record_ids.name_get()
        else:
            return res