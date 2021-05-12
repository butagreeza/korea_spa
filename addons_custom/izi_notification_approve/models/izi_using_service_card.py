# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from odoo.exceptions import except_orm, ValidationError, UserError

class ServiceCardUsing(models.Model):
    _inherit = 'izi.service.card.using'

    @api.multi
    def action_send_price(self):
        res = super(ServiceCardUsing, self).action_send_price()
        users = self.env['res.users'].search([
            ('groups_id', 'in', self.env.ref('izi_res_permissions.group_leader_shop').id),
            ('id', '!=', self._uid)])
        for line in users:
            if line.x_pos_config_id.id == self.session_id.config_id.id:
                self.schedule_activity('Sử dụng dịch vụ', line.id, self.date_order, self.id)
        self.schedule_activity('Sử dụng dịch vụ', self._uid, self.date_order, self.id)
        return res

    @api.multi
    def action_manager_confirm(self):
        res = super(ServiceCardUsing, self).action_manager_confirm()
        res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'izi.service.card.using')]).id
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
    def action_back(self):
        res = super(ServiceCardUsing, self).action_back()
        res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'izi.service.card.using')]).id
        activity_ids = self.env['mail.activity'].sudo().search(
            [('res_model_id', '=', res_model_id), ('res_id', '=', self.id)])
        if len(activity_ids) > 0:
            activity_ids.sudo().action_done()
        return res

    @api.multi
    def action_confirm_card(self):
        res = super(ServiceCardUsing, self).action_confirm_card()
        param_obj = self.env['ir.config_parameter']
        code = param_obj.get_param('default_code_product_category_material')
        if not code:
            raise ValidationError(
                _(
                    u"Bạn chưa cấu hình thông số hệ thống cho mã nhóm xuất NVL là default_code_product_category_material. Xin hãy liên hệ với người quản trị."))
        list = code.split(',')
        count_service_bom = 0
        count_service_viet = 0
        for line in self.service_card_ids:
            if line.service_id.product_tmpl_id.categ_id.x_category_code in list:
                count_service_viet += 1
            if line.service_id.bom_service_count > 1:
                count_service_bom += 1
        if count_service_viet != 0:
            if count_service_bom == 0:
                # Thông báo cho bộ phận kho
                users = self.env['res.users'].search([
                    ('groups_id', 'in', self.env.ref('izi_res_permissions.group_inventory_accounting').id),
                    ('id', '!=', self._uid)])
                for line in users:
                    if line.x_pos_config_id.id == self.session_id.config_id.id:
                        self.schedule_activity_inventory('Xuất kho NVL', line.id, self.redeem_date, self.id)
        return res

    @api.multi
    def action_confirm_service(self):
        res = super(ServiceCardUsing, self).action_confirm_service()
        param_obj = self.env['ir.config_parameter']
        code = param_obj.get_param('default_code_product_category_material')
        if not code:
            raise ValidationError(
                _(
                    u"Bạn chưa cấu hình thông số hệ thống cho mã nhóm xuất NVL là default_code_product_category_material. Xin hãy liên hệ với người quản trị."))
        list = code.split(',')
        count_service_bom = 0
        count_service_viet = 0
        for line in self.service_card1_ids:
            if line.service_id.product_tmpl_id.categ_id.x_category_code in list:
                count_service_viet += 1
            if line.service_id.bom_service_count > 1:
                count_service_bom += 1
        if count_service_viet != 0:
            if count_service_bom == 0:
                # Thông báo cho bộ phận kho
                users = self.env['res.users'].search([
                    ('groups_id', 'in', self.env.ref('izi_res_permissions.group_inventory_accounting').id),
                    ('id', '!=', self._uid)])
                for line in users:
                    if line.x_pos_config_id.id == self.session_id.config_id.id:
                        self.schedule_activity_inventory('Xuất kho NVL', line.id, self.redeem_date, self.id)
        return res


    @api.multi
    def action_confirm_guarantee(self):
        res = super(ServiceCardUsing, self).action_confirm_guarantee()
        param_obj = self.env['ir.config_parameter']
        code = param_obj.get_param('default_code_product_category_material')
        if not code:
            raise ValidationError(
                _(
                    u"Bạn chưa cấu hình thông số hệ thống cho mã nhóm xuất NVL là default_code_product_category_material. Xin hãy liên hệ với người quản trị."))
        list = code.split(',')
        count_service_bom = 0
        count_service_viet = 0
        for line in self.service_card1_ids:
            if line.service_id.product_tmpl_id.categ_id.x_category_code in list:
                count_service_viet += 1
            if line.service_id.bom_service_count > 1:
                count_service_bom += 1
        if count_service_viet != 0:
            if count_service_bom == 0:
                # Thông báo cho bộ phận kho
                users = self.env['res.users'].search([
                    ('groups_id', 'in', self.env.ref('izi_res_permissions.group_inventory_accounting').id),
                    ('id', '!=', self._uid)])
                for line in users:
                    if line.x_pos_config_id.id == self.session_id.config_id.id:
                        self.schedule_activity_inventory('Xuất kho NVL', line.id, self.redeem_date, self.id)
        return res


    @api.multi
    def action_done(self):
        res = super(ServiceCardUsing, self).action_done()
        res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'izi.service.card.using')]).id
        activity_ids = self.env['mail.activity'].sudo().search(
            [('res_model_id', '=', res_model_id), ('res_id', '=', self.id)])
        if len(activity_ids) > 0:
            activity_ids.sudo().action_done()
        return res

    def schedule_activity(self, summary, user_id, to_date, sid):
        res_model_id = self.env['ir.model'].search([('model', '=', 'izi.service.card.using')]).id
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


    def schedule_activity_inventory(self, summary, user_id, to_date, sid):
        res_model_id = self.env['ir.model'].search([('model', '=', 'pos.user.material')]).id
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