# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import timedelta, datetime, date
from odoo.exceptions import ValidationError, except_orm, UserError


class UseServiceCard(models.Model):
    _inherit = 'izi.service.card.using'


    def do_create_service_remind(self, service_card_using_ids):
        service_card_usings = self.env['izi.service.card.using'].search([('id', 'in', service_card_using_ids)])
        for service_card in service_card_usings:
            #todo kiểm tra xem có dịch vụ nào cấu hình nhắc lịch hay không?
            check = False
            arr_service_remind = []
            if service_card.type in ('service', 'guarantee', 'guarantee_bundle'):
                for line in service_card.service_card1_ids:
                    if line.service_id.x_is_remind:
                        check = True
                        arr_service_remind.append(line.service_id)
            elif service_card.type == 'card':
                for line in service_card.service_card_ids:
                    if line.service_id.x_is_remind:
                        check = True
                        arr_service_remind.append(line.service_id)
            elif service_card.type == 'bundle':
                for line in service_card.service_bundle_ids:
                    if line.service_id.x_is_remind:
                        check = True
                        arr_service_remind.append(line.service_id)
            else:
                raise UserError("Đơn sử dụng dịch vụ %s có loại (%s) chưa được cấu hình. Liên hệ Admin để được giải quyết" % (service_card.name, service_card.type))


            #todo nếu có nhắc lịch thì tạo nhắc lịch (activity.history)
            if check:
                for service_remind in arr_service_remind:
                    # todo kiểm tra và lấy cầu hình nhắc lịch trên dịch vụ
                    if service_remind.x_service_remind_ids:
                        config_remind = service_remind.get_config_remind(service_remind.x_service_remind_ids)
                    # todo kiểm tra và lấy cầu hình nhắc lịch trên nhóm dịch vụ
                    elif service_remind.categ_id.x_product_categ_remind_ids:
                        config_remind = service_remind.get_config_remind(
                            service_remind.categ_id.x_product_categ_remind_ids)
                    else:
                        raise UserError(_("Dịch vụ %s cần nhắc lịch nhưng chưa cấu hình cho dịch vụ đó") % str(
                            service_remind.default_code))
                    #todo tạo lịch nhắc
                    for config in config_remind:
                        if not config['repeat']:
                            #tìm các lịch trùng để gộp
                            date_deadline = timedelta(days=config['date_number']) + datetime.strptime(
                                service_card.redeem_date, '%Y-%m-%d %H:%M:%S')
                            #lịch nhắc khi đối tượng là CSKH
                            resource_id = self.env['activity.history.resource'].search([('code', '=', 'using_service')],
                                                                                       limit=1)
                            if service_card.therapy_record_id:
                                if service_card.therapy_record_id.state in ['stop_care', 'cancel']:
                                    break
                                else:
                                    therapy_record_id = service_card.therapy_record_id.id
                            else:
                                therapy_record_id = False
                            if config['object'] == 'customer_care':
                                self.env['activity.history'].create({
                                    'therapy_record_id': therapy_record_id,
                                    'partner_id': service_card.customer_id.id,
                                    'mail_activity_type_id': config['activity_type_id'],
                                    'type': config['type'],
                                    'object': config['object'],
                                    'user_id': False,
                                    'date_deadline': date_deadline,
                                    'is_activity_constant': True,
                                    'product_id': service_remind.id,
                                    'resource_ids': [(6, 0, [resource_id.id])],
                                    'using_id': service_card.id,
                                    'note': config['note'],
                                })
                            #lịch nhắc khi đối tượng là TVV
                            else:
                                if config['object'] == 'consultant':
                                    object = 'special_caregiver' if service_card.customer_id.x_special_caregiver else 'consultant'
                                    user = service_card.customer_id.x_special_caregiver.id if service_card.customer_id.x_special_caregiver else service_card.customer_id.user_id.id
                                else:
                                    object = 'consultant'
                                    user = service_card.customer_id.user_id.id

                                activity = service_card.env['activity.history'].create({
                                    'therapy_record_id': therapy_record_id,
                                    'partner_id': service_card.customer_id.id,
                                    'mail_activity_type_id': config['activity_type_id'],
                                    'type': config['type'],
                                    'object': object,
                                    'method_interaction': 'proactive',
                                    'user_id': user,
                                    'date_deadline': date_deadline,
                                    'is_activity_constant': True,
                                    'product_id': service_remind.id,
                                    'resource_ids': [(6, 0, [resource_id.id])],
                                    'using_id': service_card.id,
                                    'note': config['note'],
                                })
                                #todo gọi luôn hàm giao TVV
                                activity.action_assign()


    @api.multi
    def action_done(self):
        super(UseServiceCard, self).action_done()
        for service_card in self:
            #todo kiểm tra xem có dịch vụ nào cấu hình nhắc lịch hay không?
            check = False
            arr_service_remind = []

            if service_card.type in ('service', 'guarantee', 'guarantee_bundle'):
                remain_qty = -1
                for line in service_card.service_card1_ids:
                    if line.service_id.x_is_remind:
                        check = True
                        arr_service_remind.append(line.service_id)
            elif service_card.type == 'card':
                for line in service_card.service_card_ids:
                    remain_qty = line.paid_count - line.quantity - line.used_count
                    if line.service_id.x_is_remind:
                        check = True
                        arr_service_remind.append(line.service_id)
            elif service_card.type == 'bundle':
                for line in service_card.service_bundle_ids:
                    if line.service_id.x_is_remind:
                        prescription_product = service_card.therapy_prescription_id.therapy_prescription_line_remain_ids.filtered(lambda x:x.product_id == line.service_id and x.order_id == line.x_order_id and x.order_line_id == line.x_order_line_id)
                        remain_qty = prescription_product.qty_available - prescription_product.qty
                        check = True
                        arr_service_remind.append(line.service_id)
            else:
                raise UserError("Đơn sử dụng dịch vụ %s có loại (%s) chưa được cấu hình. Liên hệ Admin để được giải quyết" % (service_card.name))

            #todo nếu có nhắc lịch thì tạo nhắc lịch (activity.history)
            if check:
                for service_remind in arr_service_remind:
                    #todo kiểm tra và lấy cầu hình nhắc lịch trên dịch vụ
                    if service_remind.x_service_remind_ids:
                        config_remind = service_remind.get_config_remind(service_remind.x_service_remind_ids)
                    #todo kiểm tra và lấy cầu hình nhắc lịch trên nhóm dịch vụ
                    elif service_remind.categ_id.x_product_categ_remind_ids:
                        config_remind = service_remind.get_config_remind(service_remind.categ_id.x_product_categ_remind_ids)
                    else:
                        raise UserError(_("Dịch vụ %s cần nhắc lịch nhưng chưa cấu hình cho dịch vụ đó") % str(service_remind.default_code))
                    #todo tạo lịch nhắc
                    for config in config_remind:
                        if not config['repeat']:
                            date_deadline = timedelta(days=config['date_number']) + datetime.strptime(
                                service_card.redeem_date, '%Y-%m-%d %H:%M:%S')
                            #lịch nhắc khi đối tượng là CSKH
                            resource_id = self.env['activity.history.resource'].search([('code', '=', 'using_service')],
                                                                                       limit=1)
                            #kiểm tra nếu đơn sddv gắn hstl thì phải ktra thêm điều kiện hstl ở trạng thái khác dừng chăm sóc và hủy
                            if service_card.therapy_record_id:
                                if service_card.therapy_record_id.state in ['stop_care', 'cancel']:
                                    break
                                else:
                                    therapy_record_id = service_card.therapy_record_id.id
                            else:
                                therapy_record_id = False
                            # if config['type'] == 'do_service' and remain_qty <= 0:
                            #     break
                            if config['object'] == 'customer_care':
                                remind = self.env['activity.history'].create({
                                    'therapy_record_id': therapy_record_id,
                                    'partner_id': service_card.customer_id.id,
                                    'mail_activity_type_id': config['activity_type_id'],
                                    'type': config['type'],
                                    'object': 'special_caregiver' if service_card.customer_id.x_special_caregiver else config['object'],
                                    'user_id': service_card.customer_id.x_special_caregiver.id if service_card.customer_id.x_special_caregiver else False,
                                    'date_deadline': date_deadline,
                                    'is_activity_constant': True,
                                    'product_id': service_remind.id,
                                    'resource_ids': [(6, 0, [resource_id.id])],
                                    'using_id': service_card.id,
                                    'note': config['note'],
                                })
                                if remind.user_id:
                                    remind.action_assign()
                            #lịch nhắc khi đối tượng là TVV
                            else:
                                activity = service_card.env['activity.history'].create({
                                    'therapy_record_id': therapy_record_id,
                                    'partner_id': service_card.customer_id.id,
                                    'mail_activity_type_id': config['activity_type_id'],
                                    'type': config['type'],
                                    'object': 'special_caregiver' if service_card.customer_id.x_special_caregiver else config['object'],
                                    'method_interaction': 'proactive',
                                    'user_id': service_card.customer_id.x_special_caregiver.id if service_card.customer_id.x_special_caregiver else service_card.customer_id.user_id.id,
                                    'date_deadline': date_deadline,
                                    'is_activity_constant': True,
                                    'product_id': service_remind.id,
                                    'resource_ids': [(6, 0, [resource_id.id])],
                                    'using_id': service_card.id,
                                    'note': config['note'],
                                })
                                #todo gọi luôn hàm giao TVV
                                activity.action_assign()

    @api.multi
    def process_refund(self):
        super(UseServiceCard, self).process_refund()
        reminds_created = self.env['activity.history'].search([('using_id', '=', self.id)])
        for remind_created in reminds_created.filtered(lambda remind:remind.state != 'interacted'):
                remind_created.state = 'cancel'
                mail_acti_ids = self.env['mail.activity'].search([('res_id', '=', remind_created.id), (
                'res_model_id', '=', self.env.ref('izi_crm_interaction.model_activity_history').id)])
                for mail_id in mail_acti_ids:
                    mail_id.unlink()