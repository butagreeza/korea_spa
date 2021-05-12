# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import except_orm, ValidationError, UserError
from odoo.osv import expression
from odoo import sys, os
import base64, time
from os.path import join
from datetime import datetime, date
from odoo import http
from odoo.osv.orm import setup_modifiers
from dateutil.relativedelta import relativedelta


class PartnerTransferStage(models.TransientModel):
    _name = 'partner.transfer.stage'

    partner_id = fields.Many2one('res.partner', string="Partner")
    stage_id = fields.Many2one('crm.stage', string="Stage")
    next_interaction_reminder_activity_type_id = fields.Many2one('mail.activity.type', string="Next interaction reminder activity type")
    next_interaction_reminder_date = fields.Date(string="Next interaction reminder date")

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        if not self.stage_id or not self.stage_id.x_day_number_remind:
            return {'value': {'next_interaction_reminder_date': False}}
        else:
            next_interaction_reminder_date = date.today() + relativedelta(days=self.stage_id.x_day_number_remind)
            return {'value': {'next_interaction_reminder_date': next_interaction_reminder_date}}

    @api.multi
    def action_confirm_transfer_stage(self):
        if self.partner_id.x_stage_id.id != self.stage_id.id:
            self.env['partner.stage.history'].create({
                'partner_id': self.partner_id.id,
                'time_change': datetime.now(),
                'from_stage_id': self.partner_id.x_stage_id.id,
                'from_stage_name': self.partner_id.x_stage_id.name,
                'to_stage_id': self.stage_id.id,
                'to_stage_name': self.stage_id.name,
                'user_id': self._uid,
            })
        if self.stage_id.x_day_number_remind:
            if not self.next_interaction_reminder_date: raise UserError("Trạng thái này phải đặt lịch chăm sóc, vui lòng nhập ngày nhắc lịch.")
            if not self.next_interaction_reminder_activity_type_id: raise UserError("Trạng thái này phải đặt lịch chăm sóc, vui lòng nhập loại tương tác.")
            if not self.partner_id.x_telesales_id: raise UserError("Trạng thái này phải đặt lịch chăm sóc, vui lòng giao telesales chăm sóc trước khi chuyển trạng thái.")
            self.env['mail.activity'].create({
                'activity_type_id': self.next_interaction_reminder_activity_type_id.id,
                'res_model_id': self.env.ref('res_partner_custom.model_res_partner').id,
                'res_model': self.env.ref('res_partner_custom.model_res_partner').name,
                'res_id': self.partner_id.id,
                'user_id': self.partner_id.x_telesales_id.id,
                'date_deadline': self.next_interaction_reminder_date,
            })
            self.partner_id.write({
                'x_stage_id': self.stage_id.id,
                'x_next_interaction_reminder_activity_type_id': self.next_interaction_reminder_activity_type_id.id,
                'x_next_interaction_reminder_date': self.next_interaction_reminder_date,
            })
        else:
            user_login = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
            team_login_ids = self.env['crm.team'].get_team_ids_by_branches([user_login.branch_id and user_login.branch_id.id or 0])
            user_id = self.partner_id.user_id and self.partner_id.user_id.id or user_login.id
            team_id = False
            if self.stage_id.x_code == 'won':
                # if not self.partner_id.state_id: raise UserError("Bạn chưa nhập tỉnh thành của khách hàng!")
                if not self.partner_id.x_crm_team_id:
                    if not user_login.branch_id: raise except_orm('Thông báo', 'Người dùng %s chưa chọn chi nhánh. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                               str(user_login.name)))
                    team_id = team_login_ids[0]
                else:
                    team_id = self.partner_id.x_crm_team_id.id

                team = self.env['crm.team'].search([('id', '=', team_id)], limit=1)
                if not team: raise UserError("Không tồn tại cơ sở làm dịch vụ có id = %s" % (str(team_id)))
                #Tạo mã KH
                if self.partner_id.x_code:
                    partner_code = self.partner_id.x_code.strip().upper()
                else:
                    partner_code = self.partner_id._generate_customer_code(team.x_branch_id.code).strip().upper()
                if self.partner_id.x_old_code:
                    partner_old_code = self.partner_id.x_old_code.strip().upper()
                else:
                    partner_old_code = partner_code
                self.partner_id.write({
                    'x_code': partner_code,
                    'x_old_code': partner_old_code,
                })
            self.partner_id.write({
                'x_stage_id': self.stage_id.id,
                'user_id': user_id,
                'x_crm_team_id': team_id,
            })
