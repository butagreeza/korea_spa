# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import timedelta, datetime, date
from odoo.exceptions import ValidationError, except_orm, UserError


class ActivityHistory(models.Model):
    _name = 'activity.history'
    _description = 'Activity History'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', related='partner_id.name', readonly=True)
    therapy_record_id = fields.Many2one('therapy.record', string='Therapy Record', track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='User', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Partner', track_visibility='onchange')
    mail_activity_type_id = fields.Many2one('mail.activity.type', string='Mail Activity Type', track_visibility='onchange')
    type = fields.Selection([('out_of_medicine', 'Out of medicine'), ('customer_care', 'Customer care'),
                             ('do_service', 'Do service'), ('send_nutrition', 'Send Nutrition'), ('call_telesale', 'Call Telesale')],
                            string='Type', track_visibility='onchange')
    object = fields.Selection([('consultant', 'Consultant'), ('customer_care', 'Customer care'),
                               ('telesale', 'Telesale'), ('special_caregiver', 'special Caregiver')], string='Object', track_visibility='onchange')
    date_deadline = fields.Date(string='Date Deadline', track_visibility='onchange')
    partner_interaction_id = fields.Many2one('partner.interaction', string='Partner Interaction', track_visibility='onchange')
    state = fields.Selection([('new', 'New'), ('assigned', 'Assigned'), ('move_remind', 'Move Remind'), ('interacted', 'Interacted'), ('cancel', 'Cancel')], string='State', default='new', track_visibility='onchange')
    color = fields.Integer('Color Index', compute="_check_color", track_visibility='onchange')
    is_activity_constant = fields.Boolean(string='Is activity constant', default=False, track_visibility='onchange')
    note = fields.Text(string='Note', track_visibility='onchange')
    schedule_transfer_reason_id = fields.Many2one('schedule.transfer.reason', string='Schedule Transfer Reason', track_visibility='onchange')
    date_move_remind = fields.Date(string="Date Move Remind", default=False, track_visibility='onchange')
    product_id = fields.Many2one('product.product', string="Product")
    picking_id = fields.Many2one('stock.picking', string='Stock Picking')
    using_id = fields.Many2one('izi.service.card.using', string='Service Card Using')
    resource_ids = fields.Many2many('activity.history.resource', string='Resource')
    is_using_service = fields.Boolean(string='Is using service', default='False', compute='check_invisible')
    is_picking = fields.Boolean(string='Is picking', default='False', compute='check_invisible')
    user_transfer = fields.Many2one('res.users', string='User Transfer')

    @api.depends('picking_id', 'using_id')
    def check_invisible(self):
        if self.picking_id:
            self.is_picking = True
        else:
            self.is_picking = False
        if self.using_id:
            self.is_using_service = True
        else:
            self.is_using_service = False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        return {
            'value': {
                'therapy_record_id': False
            }
        }

    def _check_color(self):
        for record in self:
            color = 0
            if record.state == 'new':
                color = 1
            elif record.state == 'assigned':
                color = 3
            elif record.state == 'interacted':
                color = 4
            else:
                color = 5
            record.color = color

    @api.multi
    def action_assign(self):
        for activity in self:
            if activity.state == 'new':
                if not activity.user_id:
                    ctx = self.env.context.copy()
                    view = self.env.ref('izi_crm_interaction.assign_user_form_view')
                    return {
                        'name': _('Assign'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'activity.history',
                        'res_id': self.id,
                        'views': [(view.id, 'form')],
                        'view_id': view.id,
                        'target': 'new',
                        'context': ctx,
                    }
                else:
                    activity.action_confirm_assign()
                    activity.state = 'assigned'
            else:
                ctx = self.env.context.copy()
                view = self.env.ref('izi_crm_interaction.assign_user_form_view')
                return {
                    'name': _('Reason'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'activity.history',
                    'res_id': self.id,
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'context': ctx,
                }

    @api.multi
    def action_confirm_assign(self):
        if self.state in ['new', 'assigned']:
            self.state = 'assigned'
            date_deadline = self.date_deadline
        elif self.state in ['move_remind']:
            date_deadline = self.date_move_remind
        else:
            raise UserError("Bạn đang giao việc cho lịch nhắc ở trạng thái %s, vui lòng liên hệ Admin!" % (str(self.state)))

        mail_activity = self.env['mail.activity'].search([('res_id', '=', self.id), ('date_deadline', '=', date_deadline)], limit=1)
        if mail_activity: mail_activity.unlink()

        self.env['mail.activity'].create({
            'activity_type_id': self.mail_activity_type_id.id,
            'res_model_id': self.env.ref('izi_crm_interaction.model_activity_history').id,
            'res_model': self.env.ref('izi_crm_interaction.model_activity_history').name,
            'res_id': self.id,
            'user_id': self.user_id.id,
            'date_deadline': date_deadline,
        })

    def action_create_interaction(self):
        self.ensure_one()
        if not self.user_id:
            raise UserError('Bạn chưa giao nhắc lịch cho nhân viên nào! Vui lòng kiểm tra lại.')
        ctx = self.env.context.copy()
        if self.date_move_remind:
            expected_date = self.date_move_remind
        else:
            expected_date = self.date_deadline
        ctx.update({
            # 'default_method_interaction': 'proactive',
            'default_partner_id': self.partner_id.id,
            'default_activity_history_ids': [(6, 0, [self.id])],
            'default_user_id': self.user_id.id,
            'default_expected_date': expected_date,
            'default_mail_activity_type_id': self.mail_activity_type_id.id,
            'default_type': self.type,
            'default_object': self.object,
            'default_therapy_record_ids': [(6, 0, [self.therapy_record_id.id])] if self.therapy_record_id else False,
            'default_product_ids': [(6, 0, [self.product_id.id])] if self.product_id else False,
            'default_using_ids': [(6, 0, [self.using_id.id])] if self.using_id else False,
            'default_picking_ids': [(6, 0,[self.picking_id.id])] if self.picking_id else False,
        })
        view = self.env.ref('izi_crm_interaction.partner_interaction_form_view')
        return {
            'name': _('Partner Interaction'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'partner.interaction',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': '',
            'context': ctx,
        }

    def schedule_transfer(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.update({
            'default_activity_history_id': self.id,
        })
        # ctx.append
        view = self.env.ref('izi_crm_interaction.schedule_transfer_reason_form_view')
        return {
            'name': _('Reason'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'activity.history.assign',
            'res_id': False,
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

    def cancel_activity_history(self):
        if self.state == 'cancel':
            raise UserError('Nhắc lịch đã thay đổi trạng thái. Vui lòng F5 kiểm tra lại!')
        elif self.state == 'interacted':
            raise UserError('Nhắc lịch %s đã tạo tương tác nên không thể hủy được nhắc lịch này. Vui lòng kiểm tra lại!')
        else:
            self.state = 'cancel'
            mail_acti_ids = self.env['mail.activity'].search([('res_id', '=', self.id), ('res_model_id', '=', self.env.ref('izi_crm_interaction.model_activity_history').id)])
            for mail_id in mail_acti_ids:
                mail_id.unlink()

class ActivityHistoryAssign(models.TransientModel):
    _name = 'activity.history.assign'

    user_id = fields.Many2one('res.users', string='User')
    activity_history_id = fields.Many2one('activity.history', string='Activity History')
    schedule_transfer_reason_id = fields.Many2one('schedule.transfer.reason', string='Schedule Transfer Reason',
                                                  track_visibility='onchange')
    date_move_remind = fields.Date(string="Date Move Remind", default=False, track_visibility='onchange')

    @api.multi
    def assign_activity(self):
        for activity in self:
            activity_ids = activity._context.get('active_ids')
            for activity_id in activity_ids:
                activity_history = activity.env['activity.history'].search([('id', '=', activity_id)])
                if activity_history.state == 'interacted':
                    raise UserError(_('Nhắc lịch cho %s đã tạo tương tác') % activity_history.partner_id.name)
                activity_history.update({
                    'user_id': activity.user_id.id,
                })
                activity_history.action_assign()

    def confirm_transfer(self):
        if self.activity_history_id:
            self.activity_history_id.update({
                'state': 'move_remind',
                'schedule_transfer_reason_id': self.schedule_transfer_reason_id.id,
                'date_move_remind': self.date_move_remind,
                'user_transfer': self.uid,
            })
            if self.user_id:
                mail_activity = self.env['mail.activity'].search([('res_id', '=', self.activity_history_id.id), ('user_id', '=', self.user_id.id)], limit=1)
                if mail_activity: mail_activity.unlink()
                self.env['mail.activity'].create({
                    'activity_type_id': self.activity_history_id.mail_activity_type_id.id,
                    'res_model_id': self.env.ref('izi_crm_interaction.model_activity_history').id,
                    'res_model': self.env.ref('izi_crm_interaction.model_activity_history').name,
                    'res_id': self.activity_history_id.id,
                    'user_id': self.user_id.id,
                    'date_deadline': self.date_move_remind,
                })

    def confirm_transfer_multi(self):
        activity_ids = self.env['activity.history'].search([('id', 'in', self._context.get('active_ids'))])
        if len(activity_ids) != len(activity_ids.filtered(lambda act:act.state not in ['interacted', 'cancel'])):
            raise UserError("Bạn đang giao việc cho lịch nhắc ở trạng thái đã có tương tác hoặc hủy. Vui lòng kiểm tra lại!")
        for activity_id in activity_ids:
            activity_id.write({
                'state': 'move_remind',
                'schedule_transfer_reason_id': self.schedule_transfer_reason_id.id,
                'date_move_remind': self.date_move_remind,
                'user_transfer': self.uid,
            })
            mail_activity = self.env['mail.activity'].search(
                [('res_id', '=', activity_id.id), ('user_id', '=', activity_id.user_id.id)], limit=1)
            if mail_activity: mail_activity.unlink()
            if activity_id.user_id:
                self.env['mail.activity'].create({
                    'activity_type_id': activity_id.mail_activity_type_id.id,
                    'res_model_id': self.env.ref('izi_crm_interaction.model_activity_history').id,
                    'res_model': self.env.ref('izi_crm_interaction.model_activity_history').name,
                    'res_id': activity_id.id,
                    'user_id': activity_id.user_id.id,
                    'date_deadline': self.date_move_remind,
                })

class ActivityHistoryConfirm(models.TransientModel):
    _name = 'activity.history.confirm'

    partner_id = fields.Many2one('res.partner', string='Partner')
    expected_date = fields.Date(strimg='Expected Date')
    user_id = fields.Many2one('res.users', string='User')

    @api.model
    def default_get(self, fields):
        res = super(ActivityHistoryConfirm, self).default_get(fields)
        activity_ids = self.env['activity.history'].browse(self._context.get('active_ids'))
        if not activity_ids.filtered(lambda act:act.state in ['interacted', 'cancel']):
            arr_partner = []
            arr_date = []
            arr_user = []
            if len(activity_ids) != len(activity_ids.filtered(lambda acti:acti.state in ['assigned', 'move_remind'])):
                raise UserError(
                    'Chỉ được tạo tương tác cho các nhắc lịch ở trạng thái đã giao hoặc chuyển lịch. Vui lòng kiểm tra lại các nhắc lịch đã chọn')
            if len(activity_ids) != len(activity_ids.filtered(lambda acti:acti.user_id.id == self._uid)):
                raise UserError(
                    'Chỉ được tạo tương tác cho các nhắc lịch của bạn. Vui lòng kiểm tra lại các nhắc lịch đã chọn')
            for activity_id in activity_ids:
                arr_partner.append(activity_id.partner_id.id)
                if activity_id.date_move_remind:
                    arr_date.append(activity_id.date_move_remind)
                else:
                    arr_date.append(activity_id.date_deadline)
                arr_user.append(activity_id.user_id.id)
            if len(set(arr_partner)) >1:
                raise UserError('Chỉ được tạo tương tác cho các nhắc lịch cùng khách hàng. Vui lòng kiểm tra lại các nhắc lịch đã chọn')
            if len(set(arr_date)) >1:
                raise UserError('Chỉ được tạo tương tác cho các nhắc lịch cùng ngày. Vui lòng kiểm tra lại các nhắc lịch đã chọn')
            if len(set(arr_user)) >1:
                raise UserError('Chỉ được tạo tương tác cho các nhắc lịch cùng nhân viên. Vui lòng kiểm tra lại các nhắc lịch đã chọn')
            res['partner_id'] = activity_ids[0].partner_id.id
            res['user_id'] = activity_ids[0].user_id.id
            res['expected_date'] = arr_date[0]
        else:
            raise UserError(
                'Chỉ được tạo tương tác cho các nhắc lịch ở trạng thái đã giao hoặc chuyển lịch. Vui lòng kiểm tra lại các nhắc lịch đã chọn')
        return res

    def create_interaction(self):
        interaction_id = self.env['partner.interaction'].create({
            'partner_id': self.partner_id.id,
            'user_id': self.user_id.id,
            'expected_date': self.expected_date,
            'mail_activity_type_id': False,
            'activity_history_ids': [(6, 0, self._context.get('active_ids'))],
            'state': 'new',
        })
        arr_resource = []
        arr_therapy = []
        arr_product = []
        arr_picking = []
        arr_service = []

        for activity_id in self.env['activity.history'].search([('id', 'in', self._context.get('active_ids')), ('state', 'not in', ['interacted', 'cancel'])]):
            # activity_id.partner_interaction_id = interaction_id.id
            # activity_id.state = 'interacted'
            for id in activity_id.resource_ids.ids:
                arr_resource.append(id)
            if activity_id.product_id:
                arr_product.append(activity_id.product_id.id)
            if activity_id.therapy_record_id:
                arr_therapy.append(activity_id.therapy_record_id.id)
            if activity_id.picking_id:
                arr_picking.append(activity_id.picking_id.id)
            if activity_id.using_id:
                arr_service.append(activity_id.using_id.id)
        interaction_id.write({
            'therapy_record_ids': [(6, 0, set(arr_therapy))],
            'resource_ids': [(6, 0, set(arr_resource))],
            'product_ids': [(6, 0, set(arr_product))],
            'using_ids': [(6, 0, set(arr_service))],
            'picking_ids': [(6, 0, set(arr_picking))],
        })
        view = self.env.ref('izi_crm_interaction.partner_interaction_form_view')
        return {
            'name': _('Partner Interaction'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'partner.interaction',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            'res_id': interaction_id.id,
        }

class ActivityHistoryResource(models.Model):
    _name = 'activity.history.resource'

    name = fields.Char(string='Name Resource')
    code = fields.Char(string='Code resource')
    acti_history_id = fields.Many2one('activity.history', string='Activity History')
    interaction_id = fields.Many2one('partner.interaction', string='Partner interaction')

    @api.model_cr
    def init(self):
        if not self.env['activity.history.resource'].search([('code', '=', 'using_service')], limit=1):
            self.env['activity.history.resource'].create({
                'name': _('Đơn sử dụng dịch vụ'),
                'code': 'using_service',
            })
        if not self.env['activity.history.resource'].search([('code', '=', 'transfer_tele')], limit=1):
            self.env['activity.history.resource'].create({
                'name': _('Chuyển Telesalse'),
                'code': 'transfer_tele',
            })
        if not self.env['activity.history.resource'].search([('code', '=', 'stock_picking')], limit=1):
            self.env['activity.history.resource'].create({
                'name': _('Đơn xuất kho'),
                'code': 'stock_picking',
            })