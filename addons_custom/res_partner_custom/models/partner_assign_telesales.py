# -*- coding: utf-8 -*-
from odoo import models, api, fields , _
from odoo.exceptions import except_orm, ValidationError, UserError
from odoo.osv import expression
from odoo import sys, os
import base64, time
from os.path import  join
from datetime import datetime,date
import logging, re
from odoo import http
from odoo.osv.orm import setup_modifiers
from dateutil.relativedelta import relativedelta


class PartnerAssignTelesales(models.TransientModel):
    _name = 'partner.assign.telesales'

    partner_id = fields.Many2one('res.partner', string="Partner")
    telesales_id = fields.Many2one('res.users', string="Telesales")
    next_interaction_reminder_activity_type_id = fields.Many2one('mail.activity.type', string="Next interaction reminder activity type")
    next_interaction_reminder_date = fields.Date(string="Next interaction reminder date", default=fields.Date.today())

    @api.multi
    def action_confirm_assign_telesales(self):
        self.partner_id.write({
            'x_telesales_id': self.telesales_id.id,
            'x_next_interaction_reminder_activity_type_id': self.next_interaction_reminder_activity_type_id.id,
            'x_next_interaction_reminder_date': self.next_interaction_reminder_date,
        })
        self.env['mail.activity'].create({
            'activity_type_id': self.next_interaction_reminder_activity_type_id.id,
            'res_model_id': self.env.ref('res_partner_custom.model_res_partner').id,
            'res_model': self.env.ref('res_partner_custom.model_res_partner').name,
            'res_id': self.partner_id.id,
            'user_id': self.telesales_id.id,
            'date_deadline': self.next_interaction_reminder_date,
        })

class PartnerAssignTelesalesHistory(models.TransientModel):
    _name = 'partner.assign.telesales.history'

    telesales_id = fields.Many2one('res.users', string="Telesales")
    next_interaction_reminder_activity_type_id = fields.Many2one('mail.activity.type',
                                                                 string="Next interaction reminder activity type")
    next_interaction_reminder_date = fields.Date(string="Next interaction reminder date", default=fields.Date.today())

    @api.multi
    def action_confirm_assign_telesales_multi(self):
        for partner in self:
            if not partner.telesales_id:
                raise UserError(_('Bạn chưa chọn nhân viên thực hiện'))
            arr_partner = partner._context.get('active_ids')
            for partner in arr_partner:
                partner_id = self.env['res.partner'].search([('id', '=', partner)])
                if partner_id.x_telesales_id:
                    raise UserError(_('Khách hàng %s đã được giao cho chuyên viên telesale %s') % (partner_id.name, partner_id.x_telesales_id.name))
                partner_id.write({
                    'x_telesales_id': self.telesales_id.id,
                    'x_next_interaction_reminder_activity_type_id': self.next_interaction_reminder_activity_type_id.id,
                    'x_next_interaction_reminder_date': self.next_interaction_reminder_date,
                })
                self.env['mail.activity'].create({
                    'activity_type_id': self.next_interaction_reminder_activity_type_id.id,
                    'res_model_id': self.env.ref('res_partner_custom.model_res_partner').id,
                    'res_model': self.env.ref('res_partner_custom.model_res_partner').name,
                    'res_id': partner_id.id,
                    'user_id': self.telesales_id.id,
                    'date_deadline': self.next_interaction_reminder_date,
                })

    @api.multi
    def action_confirm_assign_telesales_again_multi(self):
        Mail_Activity_Obj = self.env['mail.activity']
        for partner in self:
            if not partner.telesales_id:
                raise UserError(_('Bạn chưa chọn nhân viên thực hiện'))
            arr_partner = partner._context.get('active_ids')
            for partner in arr_partner:
                partner_id = self.env['res.partner'].search([('id', '=', partner)])
                #xóa thông báo của nhân viên tele cũ
                activity_old_ids = Mail_Activity_Obj.search([('user_id', '=', partner_id.x_telesales_id.id), ('res_id', '=', partner_id.id)])
                if activity_old_ids:
                    for activity_old_id in activity_old_ids:
                        activity_old_id.unlink()
                #cập nhật tele mới và tạo thông báo
                partner_id.write({
                    'x_telesales_id': self.telesales_id.id,
                    'x_next_interaction_reminder_activity_type_id': self.next_interaction_reminder_activity_type_id.id,
                    'x_next_interaction_reminder_date': self.next_interaction_reminder_date,
                })
                Mail_Activity_Obj.create({
                    'activity_type_id': self.next_interaction_reminder_activity_type_id.id,
                    'res_model_id': self.env.ref('res_partner_custom.model_res_partner').id,
                    'res_model': self.env.ref('res_partner_custom.model_res_partner').name,
                    'res_id': partner_id.id,
                    'user_id': self.telesales_id.id,
                    'date_deadline': self.next_interaction_reminder_date,
                })

class PartnerAssignuserHistory(models.TransientModel):
    _name = 'partner.assign.user.history'

    user_id = fields.Many2one('res.users', string="User")
    next_interaction_reminder_activity_type_id = fields.Many2one('mail.activity.type',
                                                                 string="Next interaction reminder activity type")
    next_interaction_reminder_date = fields.Date(string="Next interaction reminder date", default=fields.Date.today())

    @api.multi
    def action_confirm_assign_user_again_multi(self):
        Mail_Activity_Obj = self.env['mail.activity']
        for partner in self:
            if not partner.user_id:
                raise UserError(_('Bạn chưa chọn nhân viên chăm sóc'))
            arr_partner = partner._context.get('active_ids')
            for partner in arr_partner:
                partner_id = self.env['res.partner'].search([('id', '=', partner)])
                #xóa thông báo của nhân viên tele cũ
                activity_old_ids = Mail_Activity_Obj.search([('user_id', '=', partner_id.user_id.id), ('res_id', '=', partner_id.id)])
                if activity_old_ids:
                    for activity_old_id in activity_old_ids:
                        activity_old_id.unlink()
                #cập nhật tele mới và tạo thông báo
                partner_id.write({
                    'user_id': self.user_id.id,
                    'x_next_interaction_reminder_activity_type_id': self.next_interaction_reminder_activity_type_id.id,
                    'x_next_interaction_reminder_date': self.next_interaction_reminder_date,
                })
                Mail_Activity_Obj.create({
                    'activity_type_id': self.next_interaction_reminder_activity_type_id.id,
                    'res_model_id': self.env.ref('res_partner_custom.model_res_partner').id,
                    'res_model': self.env.ref('res_partner_custom.model_res_partner').name,
                    'res_id': partner_id.id,
                    'user_id': self.user_id.id,
                    'date_deadline': self.next_interaction_reminder_date,
                })