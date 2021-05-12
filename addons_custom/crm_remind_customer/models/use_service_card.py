# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import timedelta, datetime, date

class UseServiceCard(models.Model):
    _inherit = 'izi.service.card.using'

    @api.multi
    def action_done(self):
        super(UseServiceCard, self).action_done()
        date1 = datetime.strptime(self.redeem_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
        date = date1.date()
        if self.type == 'card':
            description = ''
            for line in self.service_card_ids:
                description += line.service_id.product_tmpl_id.name + '    |     '
            for line in self.service_card_ids:
                employee_id = self.env['hr.employee']
                if self.customer_id.x_manage_user_id:
                    employee_id = self.env['hr.employee'].search(
                        ['|', ('user_id', '=', self.customer_id.x_manage_user_id.id), ('x_user_ids', 'in', [self.customer_id.x_manage_user_id.id])], limit=1)
                for tmp in line.service_id.x_service_calender_reminder_ids:
                    # nếu dịch vụ là hỏi thăm theo ngày
                    if tmp.type == 'httn':
                        # Nếu tìm thấy ngày nhắc lịch
                        service_calender_obj = self.env['crm.service.calender.reminder'].search([('date', '=', date + timedelta(days=tmp.value)), ('type', '=', 'htkh'), ('config_id', '=', self.pos_session_id.config_id.id)])
                        if service_calender_obj:
                            sevice_calender_line = self.env['crm.service.calender.reminder.line'].sudo().create({
                                'partner_id': self.customer_id.id,
                                'phone': self.customer_id.phone if self.customer_id.phone else self.customer_id.mobile,
                                'date': date,
                                'product_id': line.service_id.id,
                                'note' : '',
                                'description' : description,
                                'type' : 'card',
                                'total_quantity' : line.paid_count,
                                'quantity_used': line.used_count + line.quantity,
                                'service_calender_reminder_id': service_calender_obj.id,
                                'origin': self.name,
                                'employee_id': employee_id.id if employee_id else False,
                            })
                        # Nếu chưa tìm thấy ngày nhắc lịch thì tạo thêm
                        else:
                            service_calender_obj = self.env['crm.service.calender.reminder'].create({
                                'date': date + timedelta(days=tmp.value),
                                'type': 'htkh',
                                'config_id': self.pos_session_id.config_id.id
                            })
                            sevice_calender_line = self.env['crm.service.calender.reminder.line'].sudo().create({
                                'partner_id': self.customer_id.id,
                                'phone': self.customer_id.phone if self.customer_id.phone else self.customer_id.mobile,
                                'date': date,
                                'product_id': line.service_id.id,
                                'note': '',
                                'description': description,
                                'type': 'card',
                                'total_quantity': line.paid_count,
                                'quantity_used': line.used_count + line.quantity,
                                'service_calender_reminder_id': service_calender_obj.id,
                                'origin': self.name,
                                'employee_id': employee_id.id if employee_id else False,
                            })
                    # nếu dịch vụ là hỏi thăm theo buỏi
                    if tmp.type == 'httb':
                        # Kiểm tra dịch vụ xem có quan hệ cha con không
                        # Nếu có thì chia cho số buổi của dịch vụ cha
                        partner_product = self.env['product.product'].search([('parent_id','=', line.service_id.id)])
                        if len(partner_product) >0:
                            use_service_line = self.env['izi.service.card.using.line'].search([('service_id', '=', line.service_id.id), ('serial_id', '=', line.serial_id.id)])
                            count_use_service = 0
                            for x in use_service_line:
                                if x.using_id.state != 'cancel':
                                    count_use_service +=1
                            if count_use_service == tmp.value:
                                service_calender_obj = self.env['crm.service.calender.reminder'].search(
                                    [('date', '=', date + timedelta(days=1)), ('type', '=', 'htkh'),
                                     ('config_id', '=', self.pos_session_id.config_id.id)])
                                if service_calender_obj:
                                    sevice_calender_line = self.env['crm.service.calender.reminder.line'].sudo().create(
                                        {
                                            'partner_id': self.customer_id.id,
                                            'phone': self.customer_id.phone if self.customer_id.phone else self.customer_id.mobile,
                                            'date': date,
                                            'product_id': line.service_id.id,
                                            'note': '',
                                            'description': description,
                                            'type': 'card',
                                            'total_quantity': line.paid_count,
                                            'quantity_used': line.used_count + line.quantity,
                                            'service_calender_reminder_id': service_calender_obj.id,
                                            'origin': self.name,
                                            'employee_id': employee_id.id if employee_id else False,
                                        })
                                # Nếu chưa tìm thấy ngày nhắc lịch thì tạo thêm
                                else:
                                    service_calender_obj = self.env['crm.service.calender.reminder'].create({
                                        'date': date + timedelta(days=1),
                                        'type': 'htkh',
                                        'config_id': self.pos_session_id.config_id.id,
                                    })
                                    sevice_calender_line = self.env['crm.service.calender.reminder.line'].sudo().create(
                                        {
                                            'partner_id': self.customer_id.id,
                                            'phone': self.customer_id.phone if self.customer_id.phone else self.customer_id.mobile,
                                            'date': date,
                                            'product_id': line.service_id.id,
                                            'note': '',
                                            'description': description,
                                            'type': 'card',
                                            'total_quantity': line.paid_count,
                                            'quantity_used': line.used_count + line.quantity,
                                            'service_calender_reminder_id': service_calender_obj.id,
                                            'origin': self.name,
                                            'employee_id': employee_id.id if employee_id else False,
                                        })
                        else:
                            # Nếu tìm thấy ngày nhắc lịch
                            if line.used_count + line.quantity == tmp.value:
                                service_calender_obj = self.env['crm.service.calender.reminder'].search(
                                    [('date', '=', date + timedelta(days=1)), ('type', '=', 'htkh'), ('config_id', '=', self.pos_session_id.config_id.id)])
                                if service_calender_obj:
                                    sevice_calender_line = self.env['crm.service.calender.reminder.line'].sudo().create({
                                        'partner_id': self.customer_id.id,
                                        'phone': self.customer_id.phone if self.customer_id.phone else self.customer_id.mobile,
                                        'date': date,
                                        'product_id': line.service_id.id,
                                        'note': '',
                                        'description': description,
                                        'type': 'card',
                                        'total_quantity': line.paid_count,
                                        'quantity_used': line.used_count + line.quantity,
                                        'service_calender_reminder_id': service_calender_obj.id,
                                        'origin': self.name,
                                        'employee_id': employee_id.id if employee_id else False,
                                    })
                                # Nếu chưa tìm thấy ngày nhắc lịch thì tạo thêm
                                else:
                                    service_calender_obj = self.env['crm.service.calender.reminder'].create({
                                        'date': date + timedelta(days=1),
                                        'type': 'htkh',
                                        'config_id':self.pos_session_id.config_id.id,
                                    })
                                    sevice_calender_line = self.env['crm.service.calender.reminder.line'].sudo().create({
                                        'partner_id': self.customer_id.id,
                                        'phone': self.customer_id.phone if self.customer_id.phone else self.customer_id.mobile,
                                        'date': date,
                                        'product_id': line.service_id.id,
                                        'note': '',
                                        'description': description,
                                        'type': 'card',
                                        'total_quantity': line.paid_count,
                                        'quantity_used': line.used_count + line.quantity,
                                        'service_calender_reminder_id': service_calender_obj.id,
                                        'origin': self.name,
                                        'employee_id': employee_id.id if employee_id else False,
                                    })
                    # Nếu là nhắc lịch khách hàng đến làm dịch vụ
                    if tmp.type == 'nlkh':
                        # Nếu tìm thấy ngày nhắc lịch
                        service_calender_obj = self.env['crm.service.calender.reminder'].search(
                            [('date', '=', date + timedelta(days=tmp.value)), ('type', '=', 'nlkh'), ('config_id', '=', self.pos_session_id.config_id.id)])
                        if service_calender_obj:
                            sevice_calender_line = self.env['crm.service.calender.reminder.line'].sudo().create({
                                'partner_id': self.customer_id.id,
                                'phone': self.customer_id.phone if self.customer_id.phone else self.customer_id.mobile,
                                'date': date,
                                'product_id': line.service_id.id,
                                'note': '',
                                'description': description,
                                'type': 'card',
                                'total_quantity': line.paid_count,
                                'quantity_used': line.used_count + line.quantity,
                                'service_calender_reminder_id': service_calender_obj.id,
                                'origin': self.name,
                                'employee_id': employee_id.id if employee_id else False,
                            })
                        # Nếu chưa tìm thấy ngày nhắc lịch thì tạo thêm
                        else:
                            service_calender_obj = self.env['crm.service.calender.reminder'].create({
                                'date': date + timedelta(days=tmp.value),
                                'type': 'nlkh',
                                'config_id': self.pos_session_id.config_id.id,
                            })
                            sevice_calender_line = self.env['crm.service.calender.reminder.line'].sudo().create({
                                'partner_id': self.customer_id.id,
                                'phone': self.customer_id.phone if self.customer_id.phone else self.customer_id.mobile,
                                'date': date,
                                'product_id': line.service_id.id,
                                'note': '',
                                'description': description,
                                'type': 'card',
                                'total_quantity': line.paid_count,
                                'quantity_used': line.used_count + line.quantity,
                                'service_calender_reminder_id': service_calender_obj.id,
                                'origin': self.name,
                                'employee_id': employee_id.id if employee_id else False,
                            })
        #                 sangla them ghi chú những khách hàng đến trước ngày nhắc lịch
                        service_calender_befoce_date_obj = self.env['crm.service.calender.reminder'].search(
                            [('date', '<', date + timedelta(days=tmp.value)), ('date', '>', date ), ('type', '=', 'nlkh')])
                        for i in service_calender_befoce_date_obj:
                            for j in i.service_calender_reminder_ids:
                                if j.product_id.id == line.service_id.id and j.partner_id.id == self.customer_id.id:
                                    j.note_before_custom = 'khách hàng đến làm dịch vụ ngày' + str(date)

        if self.type == 'service':
            description = ''
            for line in self.service_card1_ids:
                description += line.service_id.product_tmpl_id.name + '\n'
            for line in self.service_card1_ids:
                employee_id = self.env['hr.employee']
                if self.customer_id.x_manage_user_id:
                    employee_id = self.env['hr.employee'].search(
                        ['|', ('user_id', '=', self.customer_id.x_manage_user_id.id),
                         ('x_user_ids', 'in', [self.customer_id.x_manage_user_id.id])], limit=1)
                for tmp in line.service_id.x_service_calender_reminder_ids:
                    # nếu dịch vụ là hỏi thăm theo ngày
                    if tmp.type == 'httn':
                        # Nếu tìm thấy ngày nhắc lịch
                        service_calender_obj = self.env['crm.service.calender.reminder'].search(
                            [('date', '=', date + timedelta(days=tmp.value)), ('type', '=', 'htkh'), ('config_id', '=', self.pos_session_id.config_id.id)])
                        if service_calender_obj:
                            sevice_calender_line = self.env['crm.service.calender.reminder.line'].sudo().create({
                                'partner_id': self.customer_id.id,
                                'phone': self.customer_id.phone if self.customer_id.phone else self.customer_id.mobile,
                                'date': date,
                                'product_id': line.service_id.id,
                                'note': '',
                                'description': description,
                                'type': 'service',
                                'total_quantity': line.paid_count,
                                'quantity_used': line.used_count + line.quantity,
                                'service_calender_reminder_id': service_calender_obj.id,
                                'origin': self.name,
                                'employee_id': employee_id.id if employee_id else False,
                            })
                        # Nếu chưa tìm thấy ngày nhắc lịch thì tạo thêm
                        else:
                            service_calender_obj = self.env['crm.service.calender.reminder'].create({
                                'date': date + timedelta(days=tmp.value),
                                'type': 'htkh',
                                'config_id': self.pos_session_id.config_id.id,
                            })
                            sevice_calender_line = self.env['crm.service.calender.reminder.line'].sudo().create({
                                'partner_id': self.customer_id.id,
                                'phone': self.customer_id.phone if self.customer_id.phone else self.customer_id.mobile,
                                'date': date,
                                'product_id': line.service_id.id,
                                'note': '',
                                'description': description,
                                'type': 'service',
                                'total_quantity': line.paid_count,
                                'quantity_used': line.used_count + line.quantity,
                                'service_calender_reminder_id': service_calender_obj.id,
                                'origin': self.name,
                                'employee_id': employee_id.id if employee_id else False,
                            })
                    # nếu dịch vụ là hỏi thăm theo buỏi
                    if tmp.type == 'httb':
                        # Nếu tìm thấy ngày nhắc lịch
                        if line.used_count + line.quantity == tmp.value:
                            service_calender_obj = self.env['crm.service.calender.reminder'].search(
                                [('date', '=', date + timedelta(days=1)), ('type', '=', 'htkh') , ('config_id', '=', self.pos_session_id.config_id.id)])
                            if service_calender_obj:
                                sevice_calender_line = self.env['crm.service.calender.reminder.line'].sudo().create({
                                    'partner_id': self.customer_id.id,
                                    'phone': self.customer_id.phone if self.customer_id.phone else self.customer_id.mobile,
                                    'date': date,
                                    'product_id': line.service_id.id,
                                    'note': '',
                                    'description': description,
                                    'type': 'service',
                                    'total_quantity': line.paid_count,
                                    'quantity_used': line.used_count + line.quantity,
                                    'service_calender_reminder_id': service_calender_obj.id,
                                    'origin': self.name,
                                    'employee_id': employee_id.id if employee_id else False,
                                })
                            # Nếu chưa tìm thấy ngày nhắc lịch thì tạo thêm
                            else:
                                service_calender_obj = self.env['crm.service.calender.reminder'].create({
                                    'date': date + timedelta(days=1),
                                    'type': 'htkh',
                                    'config_id': self.pos_session_id.config_id.id
                                })
                                sevice_calender_line = self.env['crm.service.calender.reminder.line'].sudo().create({
                                    'partner_id': self.customer_id.id,
                                    'phone': self.customer_id.phone if self.customer_id.phone else self.customer_id.mobile,
                                    'date': date,
                                    'product_id': line.service_id.id,
                                    'note': '',
                                    'description': description,
                                    'type': 'service',
                                    'total_quantity': line.paid_count,
                                    'quantity_used': line.used_count + line.quantity,
                                    'service_calender_reminder_id': service_calender_obj.id,
                                    'origin': self.name,
                                    'employee_id': employee_id.id if employee_id else False,
                                })

    @api.multi
    def action_confirm_refund(self):
        super(UseServiceCard,self).action_confirm_refund()
        date1 = datetime.strptime(self.redeem_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
        date = date1.date()
        for line in self.service_card_ids:
            for tmp in line.service_id.x_service_calender_reminder_ids:
                if tmp.type == 'nlkh':
                    #sangla them ghi chú những khách hàng đến trước ngày nhắc lịch
                    service_calender_befoce_date_obj = self.env['crm.service.calender.reminder'].search(
                        [('date', '<', date + timedelta(days=tmp.value)), ('date', '>', date), ('type', '=', 'nlkh')])
                    for i in service_calender_befoce_date_obj:
                        for j in i.service_calender_reminder_ids:
                            if j.product_id.id == line.service_id.id and j.partner_id.id == self.customer_id.id:
                                j.note_before_custom = ''
        service_remind_customer_obj = self.env['crm.service.calender.reminder.line'].sudo().search([('origin', '=', self.name)])
        for line in service_remind_customer_obj:
            line.unlink()

