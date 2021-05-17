# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError, MissingError
import logging
import json

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'


    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        picking = self.env['stock.picking'].search([('backorder_id', '=', self.id)])
        if res and res.x_therapy_record_id:
            res.update({
                'x_medicine_day_ok': False,
            })
        return res

    def create_activity_history(self):
        if self.x_therapy_record_id.state not in ['cancel', 'stop_care'] and self.x_medicine_day_ok:
            #todo cập nhật ngày hết thuốc trên HSTL
            #tinh số ngày thuốc được dùng trong PCĐ
            qty = 0
            for therapy_prescription_line_remain_id in self.x_therapy_prescription_id.therapy_prescription_line_remain_ids:
                if therapy_prescription_line_remain_id.product_id.x_is_medicine_day:
                    qty += therapy_prescription_line_remain_id.qty
            qty_remain = 1
            #kiểm tra xem có phải là ngày lấy thuốc cuối cùng không?
            # for remain_product in self.x_therapy_record_id.therapy_record_product_ids.filtered(lambda remain:remain.product_id.x_is_medicine_day):
            #     qty_remain + = remain_product.qty_available
            if self.x_therapy_record_id.out_of_medicine_date:
                out_of_date = datetime.strptime(self.x_therapy_record_id.out_of_medicine_date, '%Y-%m-%d') + timedelta(days=qty)
            else:
                out_of_date = datetime.now() + timedelta(days=qty)
                self.x_therapy_record_id.first_medicine_date = out_of_date
            #cap nhat ngày hết thuốc trên hstl
            self.x_therapy_record_id.out_of_medicine_date = out_of_date
            #nếu còn tồn ngày thuốc thì mới sinh lịch
            if qty_remain > 0:
                #todo tạo lịch nhắc thuốc sau khi xuất đơn kho
                arr = self.env['ir.config_parameter'].sudo().get_param('Remind.Medicine')
                arr_config = json.loads(arr.replace("'", "\""))
                reminds_created = self.env['activity.history'].search(
                    [('therapy_record_id', '=', self.x_therapy_record_id.id), ('state', 'not in', ['interacted', 'cancel']),
                     ('type', '=', 'out_of_medicine')], limit=1)
                date_deadline = out_of_date - timedelta(days=arr_config['date_deadline'])
                resource_id = self.env['activity.history.resource'].search([('code', '=', 'stock_picking')], limit=1)
                reminds_created_repeat_1 = reminds_created.filtered(
                    lambda remind: remind.date_deadline == date_deadline.strftime('%Y-%m-%d') and remind.date_move_remind == False)
                reminds_created_repeat_2 = reminds_created.filtered(lambda remind: remind.date_move_remind and remind.date_move_remind == date_deadline.strftime('%Y-%m-%d'))
                # nếu tồn tại lịch nhắc thì kiểm tra lại xem khách hàng có ng chăm sóc đặc biệt thì cập nhật vào lịch nhắc
                if reminds_created_repeat_1 or reminds_created_repeat_2:
                    for remind_created in reminds_created.filtered(lambda remind: remind.partner_id.x_special_caregiver):
                        remind_created.user_id = self.partner_id.x_special_caregiver.id
                else:
                    # nếu tồn tại các lịch nhắc trước hoặc sau ngày nhắc lịch của lịch mới hoặc chưa có nhắc lịch thuốc cho hstl này
                    # thì hủy đi các nhắc lịch vừa tìm và tạo lịch nhắc mới
                    user = self.env['res.users'].search([('id', '=', self._uid)])
                    for remind in reminds_created.filtered(lambda remind:remind.id not in reminds_created_repeat_1.ids and remind.id not in reminds_created_repeat_2.ids):
                        remind.state = 'cancel'
                        remind.note = f'{remind.note} - {user.name} Hủy lúc: {datetime.now() + timedelta(hours=7)}, do HSTL đã có nhắc lịch mới'
                        mail_acti_ids = self.env['mail.activity'].search([('res_id', '=', remind.id), ('res_model_id', '=', self.env.ref('izi_crm_interaction.model_activity_history').id)])
                        for mail_id in mail_acti_ids:
                            mail_id.unlink()
                    if self.x_therapy_record_id.state not in ['stop_care']:
                        remind = self.env['activity.history'].create({
                            'partner_id': self.partner_id.id,
                            'therapy_record_id': self.x_therapy_record_id.id,
                            'mail_activity_type_id': arr_config['activity_type_id'],
                            'type': 'out_of_medicine',
                            'object': 'special_caregiver' if self.partner_id.x_special_caregiver else 'consultant',
                            'user_id': self.partner_id.x_special_caregiver.id if self.partner_id.x_special_caregiver else self.partner_id.user_id.id,
                            'date_deadline': date_deadline,
                            'picking_id': self.id,
                            'resource_ids': [(6, 0, [resource_id.id])],
                        })
                        remind.action_assign()

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self):
        res = super(StockMove, self)._action_done()
        for move in self:
            pickings = move.env['stock.picking'].search([('backorder_id', '=', move.picking_id.id)])
            for picking in pickings:
                if picking and picking.x_medicine_day_ok:
                    picking.update({
                        'x_medicine_day_ok': False,
                    })
        return res