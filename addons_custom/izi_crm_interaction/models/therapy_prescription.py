# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError, MissingError
import json


class TherapyPrescription(models.Model):
    _inherit = 'therapy.prescription'

    activity_type_id = fields.Many2one('mail.activity.type', 'Activity Type')

    @api.model_cr
    def init(self):
        date_synchronize = self.env['ir.config_parameter'].search([('key', '=', 'Remind.Medicine')])
        if not date_synchronize:
            arr = {
                'date_deadline': 3,
                'activity_type_id': 2,
            }
            date_synchronize.set_param('Remind.Medicine', arr)

    def action_cancel(self):
        for stock_picking in self.stock_picking_ids.filtered(lambda sp: sp.state != 'cancel'):
            if stock_picking.x_medicine_day_ok:
                # todo cập nhật ngày hết thuốc trên HSTL
                # tinh số ngày thuốc được dùng trong PCĐ
                qty_day = 0
                for therapy_prescription_line_remain_id in self.therapy_prescription_line_remain_ids:
                    if therapy_prescription_line_remain_id.product_id.x_is_medicine_day:
                        qty_day += therapy_prescription_line_remain_id.qty
                if self.therapy_record_id.out_of_medicine_date:
                    out_of_date = datetime.strptime(self.therapy_record_id.out_of_medicine_date,
                                                    '%Y-%m-%d') - timedelta(days=qty_day)
                else:
                    out_of_date = datetime.now() - timedelta(days=qty_day) + timedelta(hours=7)
                # cap nhat ngày hết thuốc trên hstl
                if self.therapy_record_id.first_medicine_date == self.therapy_record_id.out_of_medicine_date:
                    self.therapy_record_id.out_of_medicine_date = False
                    self.therapy_record_id.first_medicine_date = False
                else:
                    self.therapy_record_id.out_of_medicine_date = out_of_date
                # hủy nhắc lịch thuốc có liên quan đến hstl
                reminds_created = self.env['activity.history'].search(
                [('therapy_record_id', '=', self.therapy_record_id.id), ('state', 'not in', ['interacted', 'cancel']),
                 ('type', '=', 'out_of_medicine')])
                if not self.therapy_record_id.out_of_medicine_date:
                    user = self.env['res.users'].search([('id', '=', self._uid)])
                    for remind_created in reminds_created:
                        remind_created.state = 'cancel'
                        remind_created.note = f'{remind_created.note} - {user.name} Hủy do HSTL không còn ngày hết thuốc lúc: {datetime.now() + timedelta(hours=7)}'
                        mail_acti_ids = self.env['mail.activity'].search([('res_id', '=', remind_created.id), (
                            'res_model_id', '=', self.env.ref('izi_crm_interaction.model_activity_history').id)])
                        for mail_id in mail_acti_ids:
                            mail_id.unlink()
                else:
                    user = self.env['res.users'].search([('id', '=', self._uid)])
                    arr = self.env['ir.config_parameter'].sudo().get_param('Remind.Medicine')
                    arr_config = json.loads(arr.replace("'", "\""))
                    date_deadline = out_of_date - timedelta(days=arr_config['date_deadline'])
                    resource_id = self.env['activity.history.resource'].search([('code', '=', 'stock_picking')], limit=1)
                    reminds_created_repeat_1 = reminds_created.filtered(lambda remind: remind.date_deadline == date_deadline.strftime('%Y-%m-%d') and remind.date_move_remind == False)
                    reminds_created_repeat_2 = reminds_created.filtered(lambda remind: remind.date_move_remind and remind.date_move_remind == date_deadline.strftime('%Y-%m-%d'))
                    # nếu tồn tại lịch nhắc thì kiểm tra lại xem khách hàng có ng chăm sóc đặc biệt thì cập nhật vào lịch nhắc
                    if reminds_created_repeat_1 or reminds_created_repeat_2:
                        for remind_created in reminds_created.filtered(
                                lambda remind: remind.partner_id.x_special_caregiver):
                            remind_created.user_id = self.partner_id.x_special_caregiver.id
                    else:
                        # nếu tồn tại các lịch nhắc trước hoặc sau ngày nhắc lịch của lịch mới hoặc chưa có nhắc lịch thuốc cho hstl này
                        # thì hủy đi các nhắc lịch vừa tìm và tạo lịch nhắc mới
                        for remind in reminds_created.filtered(lambda remind:remind.id not in reminds_created_repeat_1.ids and remind.id not in reminds_created_repeat_2.ids):
                            remind.state = 'cancel'
                            remind.note = f'{remind.note} - {user.name} Hủy lúc: {datetime.now() + timedelta(hours=7)}, do HSTL đã có nhắc lịch mới'
                            mail_acti_ids = self.env['mail.activity'].search([('res_id', '=', remind.id), (
                            'res_model_id', '=', self.env.ref('izi_crm_interaction.model_activity_history').id)])
                            for mail_id in mail_acti_ids:
                                mail_id.unlink()
                        #kiểm tra xem đã có tương tác của nhắc lịch
                        partner_interaction = self.env['partner.interaction'].search([('state', '=', 'done'),
                                                                                      ('expected_date', '=', date_deadline.date()),
                                                                                      ('therapy_record_ids', 'in', [self.therapy_record_id.id])])
                        if not partner_interaction and self.therapy_record_id.state not in ['cancel', 'stop_care']:
                            remind = self.env['activity.history'].create({
                                'partner_id': self.partner_id.id,
                                'therapy_record_id': self.therapy_record_id.id,
                                'mail_activity_type_id': arr_config['activity_type_id'],
                                'type': 'out_of_medicine',
                                'object': 'special_caregiver' if self.partner_id.x_special_caregiver else 'consultant',
                                'user_id': self.partner_id.x_special_caregiver.id if self.partner_id.x_special_caregiver else self.partner_id.user_id.id,
                                'date_deadline': date_deadline,
                                'picking_id': stock_picking.id,
                                'resource_ids': [(6, 0, [resource_id.id])],
                            })
                            remind.action_assign()


        return super(TherapyPrescription, self).action_cancel()