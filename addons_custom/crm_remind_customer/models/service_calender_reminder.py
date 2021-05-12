# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime, timedelta
from odoo.exceptions import except_orm
from odoo.exceptions import ValidationError


class ServiceCalenderReminder(models.Model):
    _name = 'crm.service.calender.reminder'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", track_visibility='onchange')
    date = fields.Date("Date", track_visibility='onchange')
    type = fields.Selection([('htkh', "HTKH"), ('nlkh', "NLKH")], track_visibility='onchange') # httk là hỏi thăm khách hang, nlkh là nhắc lịch làm khách hàng
    service_calender_reminder_ids = fields.One2many('crm.service.calender.reminder.line', 'service_calender_reminder_id', 'Service Calender')
    config_id = fields.Many2one('pos.config', "Pos Config", track_visibility='onchange')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('crm.service.calender.reminder') or _('New')
        return super(ServiceCalenderReminder, self).create(vals)

    @api.multi
    def job_service_calender(self):
        to_date = (datetime.now() + timedelta(days=1)).date()
        to_date_hoi_tham = (datetime.now()).date()
        calender_reminder_obj = self.env['crm.service.calender.reminder'].search([('date', '=', to_date)])
        calender_reminder_hoi_tham_obj = self.env['crm.service.calender.reminder'].search([('date', '=', to_date_hoi_tham)])
        for line in calender_reminder_obj:
            # res_user_ids = self.env['']
            if line.type == 'nlkh':
                name = 'Nhắc lịch khách hàng ngày ' + str(to_date)
                job = self.env['hr.job'].search([('x_code', '=', 'NVTV')], limit=1)
                if job.id == False:
                    raise except_orm('Cảnh báo!', _("Xin hãy cấu hình chức vụ nhân viên tư vấn với mã là 'NVTV'"))
                employee_ids = self.env['hr.employee'].search([('job_id', '=', job.id)])
                partner_ids = []
                date_start = datetime.now()
                date_start = date_start.replace(minute=50, hour=3, second=0)
                stop = date_start.replace(minute=30, hour=7, second=0)
                alarm_ids = self.env['calendar.alarm'].search([('id', '=', '3')])
                for tmp in employee_ids:
                    if tmp.resource_id.user_id.x_pos_config_id == line.config_id:
                        partner_ids.append(tmp.resource_id.user_id.partner_id.id)
                partner_ids.append(3)
                calender_id = self.env['calendar.event'].create({
                    'name': name,
                    'partner_ids': [(4, x) for x in partner_ids],
                    'start_datetime': date_start,
                    'duration': 4,
                    'alarm_ids': [(4, x.id) for x in alarm_ids],
                    'start': date_start,
                    'stop': stop,
                    'x_crm_remind_customer_id': line.id
                })
        for line in calender_reminder_hoi_tham_obj:
            if line.type == 'htkh':
                name = 'Hỏi thăm khách hàng ngày ' + str(to_date_hoi_tham)
                job = self.env['hr.job'].search([('x_code', '=', 'NVTV')], limit=1)
                if job.id == False:
                    raise except_orm('Cảnh báo!', _("Xin hãy cấu hình chức vụ nhân viên tư vấn với mã là 'NVTV'"))
                employee_ids = self.env['hr.employee'].search([('job_id', '=', job.id)])
                partner_ids = []
                date_start = datetime.now()
                date_start = date_start.replace(minute=30, hour=3, second=0)
                stop = date_start.replace(minute=30, hour=7, second=0)
                alarm_ids = self.env['calendar.alarm'].search([('id', '=', '3')])
                for tmp in employee_ids:
                    if tmp.resource_id.user_id.x_pos_config_id == line.config_id:
                        partner_ids.append(tmp.resource_id.user_id.partner_id.id)
                partner_ids.append(3)
                calender_id = self.env['calendar.event'].create({
                    'name': name,
                    'partner_ids': [(4, x) for x in partner_ids],
                    'start_datetime': date_start,
                    'duration': 4,
                    'alarm_ids': [(4, x.id) for x in alarm_ids],
                    'start': date_start,
                    'stop': stop,
                    'x_crm_remind_customer_id': line.id
                })
                # values['message_follower_ids'] = []
                # users = self.env['res.users'].search([
                #     ('groups_id', 'in', self.env.ref('point_of_sale.group_pos_manager').id),
                #     ('id', '!=', self._uid)])
                # MailFollowers = self.env['mail.followers']
                # follower_partner_ids = []
                # for m in self.message_follower_ids:
                #     follower_partner_ids.append(m.partner_id.id)
                # for user in users:
                #     if user.x_pos_config_id.id == self.config_id.id and \
                #             user.partner_id.id and user.partner_id.id not in follower_partner_ids:
                #         values['message_follower_ids'] += \
                #             MailFollowers._add_follower_command(self._name, [], {user.partner_id.id: None}, {})[0]
                # self.write(values)
                # self.message_post(subtype='mt_activities',
                #                   body="Đơn hàng%s cần phê duyệt!" % (' ' + ', '.join(msg) if len(msg) else ''))
                # return {'type': 'ir.actions.act_window_close'}
                # for i in partner_ids:
                #     self.schedule_activity(name, 3, to_date, line.id)

    # def schedule_activity(self, summary, user_id, to_date, sid):
    #     res_model_id = self.env['ir.model'].search([('model', '=', 'res.partner')]).id
    #     argvs = {
    #         'activity_type_id': 2,
    #         'user_id': user_id,
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
