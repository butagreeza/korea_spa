# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from odoo.exceptions import ValidationError, except_orm, UserError


class PartnerInteraction(models.Model):
    _name = 'partner.interaction'
    _description = 'Partner interaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_feedbacks(self):
        feedbacks = []
        criteria_ids = self.env['interaction.criteria'].search([('id', '!=', 0)])
        for criteria in criteria_ids:
            val = {
                'criteria_id': criteria.id
            }
            feedbacks.append(val)
        return feedbacks

    name = fields.Char(related='partner_id.name', string='Name', readonly=1, store=True)
    partner_id = fields.Many2one('res.partner', string='Partner', track_visibility='onchange')
    phone = fields.Char(related="partner_id.phone", string="Phone", readonly=True)
    activity_history_ids = fields.Many2many('activity.history', string='Activity history', track_visibility='onchange')
    therapy_record_ids = fields.Many2many('therapy.record', string='Therapy record', track_visibility='onchange')
    user_id = fields.Many2one('res.users', default=lambda self: self.env.uid, string='User',
                              track_visibility='onchange')
    expected_date = fields.Date(string="Expected date", default=fields.Date.context_today, track_visibility='onchange')
    actual_date = fields.Date(string="Actual date", default=fields.Date.context_today, track_visibility='onchange')
    date = fields.Date(related='actual_date', string='Date')
    mail_activity_type_id = fields.Many2one('mail.activity.type', string='Activity type', track_visibility='onchange')
    content = fields.Text(string='Content', track_visibility='onchange')
    read_therapy_record_start = fields.Datetime(string='Read therapy record start', track_visibility='onchange')
    read_therapy_record_end = fields.Datetime(string='Read therapy record end', track_visibility='onchange')
    read_time = fields.Float(string='Read time')
    type = fields.Selection([('out_of_medicine', 'Out of medicine'), ('customer_care', 'Customer care'),
                             ('do_service', 'Do service'), ('send_nutrition', 'Send Nutrition'), ('call_telesale', 'Call Telesale')],
                            string='Type', track_visibility='onchange')
    # object = fields.Selection([('consultant', 'Consultant'), ('customer_care', 'Customer care')], string='Object')
    object = fields.Selection([('consultant', 'Consultant'), ('customer_care', 'Customer care'),
                               ('telesale', 'Telesale'), ('special_caregiver', 'special Caregiver')], string='Object',
                              track_visibility='onchange')
    method_interaction = fields.Selection([('proactive', 'Proactive'), ('passive', 'Passive')], default=False, string='Method interaction')
    state = fields.Selection([('new', 'New'), ('reading', 'Reading'), ('processing', 'Processing'), ('done', 'Done')],
                             string='State', default='new', track_visibility='onchange')
    feedback_ids = fields.One2many('interaction.feedback', 'interaction_id', string='FeedBack', default=_default_feedbacks, track_visibility='onchange')
    resource_ids = fields.Many2many('activity.history.resource', string='Resource')
    product_ids = fields.Many2many('product.product', string='Product')
    using_ids = fields.Many2many('izi.service.card.using', string='Service Card Using')
    picking_ids = fields.Many2many('stock.picking', string='Stock Picking')


    @api.onchange('read_therapy_record_start', 'read_therapy_record_end')
    def _onchange_read_therapy_record_start_read_therapy_record_end(self):
        if self.read_therapy_record_start and self.read_therapy_record_end:
            read_therapy_record_start = datetime.strptime(self.read_therapy_record_start, '%Y-%m-%d %H:%M:%S')
            read_therapy_record_end = datetime.strptime(self.read_therapy_record_end, '%Y-%m-%d %H:%M:%S')
            self.read_time = (read_therapy_record_end-read_therapy_record_start).seconds / 60 / 60

    @api.multi
    def action_start_read_therapy_record(self):
        # '- Cập nhật "Thời gian bắt đầu đọc HS"
        # - Mở formview HSTL
        for interaction in self:
            interaction.write({
                'read_therapy_record_start': fields.Datetime.now(),
                'state': 'reading'
            })
            interaction._onchange_read_therapy_record_start_read_therapy_record_end()
            # if interaction.therapy_record_ids:
            #     view_tree_id = self.env.ref('izi_therapy_record.izi_view_therapy_record_tree').id
            #     view_form_id = self.env.ref('izi_therapy_record.izi_view_therapy_record_form').id
            #     return {
            #         'type': 'ir.actions.act_window',
            #         'res_model': 'therapy.record',
            #         'res_id': False,
            #         'name': 'Hồ sơ trị liệu',
            #         # 'view_type': 'tree',
            #         'view_mode': 'tree,form',
            #         'views': [(view_tree_id, 'tree'), (view_form_id, 'form')],
            #         'target': 'current',
            #         'domain': [('id', 'in', interaction.therapy_record_ids.ids)],
            #     }
            # else:
            view_id = self.env.ref('base.view_partner_form').id
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'res.partner',
                'res_id': interaction.partner_id.id,
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(view_id, 'form')],
                'target': 'current',
                'context': dict(self._context),
            }

    # @api.multi
    # def action_end_read_therapy_record(self):
    #     self.ensure_one()
    #     ctx = self.env.context.copy()
    #     # ctx.append
    #     view = self.env.ref('izi_crm_interaction.enter_note_interaction_form_view')
    #     return {
    #         'name': _('Reason'),
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'partner.interaction',
    #         'res_id': self.id,
    #         'views': [(view.id, 'form')],
    #         'view_id': view.id,
    #         'target': 'new',
    #         'context': ctx,
    #     }

    @api.multi
    def action_end_read_therapy_record(self):
        for interaction in self:
            if not interaction.content: raise UserError("Bạn phải nhập nội dung trước khi dừng đọc hồ sơ!")
            interaction.write({
                'read_therapy_record_end': fields.Datetime.now(),
                'state': 'processing'
            })
            interaction._onchange_read_therapy_record_start_read_therapy_record_end()

    # @api.multi
    # def action_done(self):
    #     for interaction in self:
            if interaction.activity_history_ids:
                for activity_history_id in interaction.activity_history_ids:
                    if activity_history_id.state == 'interacted':
                        raise UserError('Nhắc lịch đã ở trạng thái hoàn thành! Vui lòng kiểm tra lại tương tác của phải là tương tác duy nhất của nhắc lich %s không?' % (activity_history_id.name))
                    activity_history_id.state = 'interacted'
                    activity_history_id.partner_interaction_id = self.id
                    mail_activities = self.env['mail.activity'].search(
                        [('res_model', '=', activity_history_id._name),
                         ('res_id', '=', activity_history_id.id)])
                    if mail_activities:
                        for activity in mail_activities:
                            activity.action_done()
                    if interaction.therapy_record_ids:
                        for therapy_record_id in interaction.therapy_record_ids:
                            if activity_history_id.type == 'customer_care' and activity_history_id.object in ['customer_care','special_caregiver']:
                                therapy_record_id.interaction_last_date = interaction.actual_date
                        #gọi hàm sinh lịch tự động để xử lý lịch nhắc cũ và lịch nhắc tương lai bị lệch ngày do tương tác lệch ngày
                        is_activity_constant = True
                        if therapy_record_id.state not in ('cancel', 'stop_care'):
                            self.env['therapy.record'].create_activity_history([therapy_record_id.id], is_activity_constant)
            '''
            Tạm thời ko sử dụng
            if self.feedback_ids:
                for feedback in self.feedback_ids:
                    if not feedback.option_id:
                        raise UserError("Bạn chưa lựa chọn cho tiêu chí!")'''
            interaction.state = 'done'

    @api.multi
    def action_create_meeting(self):
        for interaction in self:
            view_id = self.env.ref('izi_crm_booking.service_booking_form_view').id
            user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
            if not user.branch_id: raise except_orm('Thông báo', 'Người dùng %s chưa chọn chi nhánh. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                           str(user.name)))
            team_ids = self.env['crm.team'].get_team_ids_by_branches([user.branch_id and user.branch_id.id or 0])
            crm_team_id = team_ids[0]
            context = {
                'default_customer_id': interaction.partner_id.id,
                'default_team_id': crm_team_id
            }
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'service.booking',
                'res_id': False,
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(view_id, 'form')],
                'target': 'new',
                'context': context
            }

    @api.multi
    def action_create_claim(self):
        for interaction in self:
            view_id = self.env.ref('izi_crm_claim.crm_claim_form_view').id
            context = {
                'default_partner_id': interaction.partner_id.id,
                'default_claim_date': fields.Datetime.now(),
            }
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'crm.claim',
                'res_id': False,
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(view_id, 'form')],
                'target': 'current',
                'context': context
            }

    @api.multi
    def action_back_to_draft(self):
        for interaction in self:
            interaction.state = 'new'
            interaction.read_therapy_record_start = None
            interaction.read_therapy_record_end = None
            interaction.read_time = None
            for activity in interaction.activity_history_ids:
                if activity.date_move_remind:
                    activity.state = 'move_remind'
                else:
                    activity.state = 'assigned'
                activity.partner_interaction_id = False

    @api.model
    def value_to_html(self, value):
        interaction_id = self.env['partner.interaction'].search([('id', '=', value)])
        hours, minutes = divmod(interaction_id.read_time * 60, 60)
        min, sec = divmod(minutes * 60, 60)
        return '%02d:%02d' % (60 * hours + min, sec)

    @api.multi
    def unlink(self):
        for interaction in self:
            if interaction.state != 'new':
                raise UserError('Tương tác không thể xóa khi khác trạng thái Mới! Vui lòng liên hệ với Trưởng phòng để được giải quyết.')
        return super(PartnerInteraction, self).unlink()


