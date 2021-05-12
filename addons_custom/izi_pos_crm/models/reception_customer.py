# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, except_orm, ValidationError
from datetime import datetime, date


class ReceptionCustomer(models.Model):
    _name = 'reception.customer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Reception customer"
    _order = 'create_date DESC'

    def _default_team_id(self):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)])
        team_id = self.env['crm.team'].search([('x_branch_id', '=', user_id.branch_id.id)], limit=1)
        return team_id

    def _default_country_id(self):
        country = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
        if not country:
            raise UserError("Chưa có quốc gia Việt Nam, vui lòng liên hệ Admin")
        return country.id

    def _domain_team_id(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        if not user: raise UserError('Không tìm thấy người dùng có id: %s' % (str(self._uid)))
        if not user.branch_id: raise UserError('Người dùng %s chưa được cấu hình chi nhánh' % (str(user.name)))
        branch_ids = [user.branch_id and user.branch_id.id or 0]
        for branch in user.branch_ids:
            branch_ids.append(branch.id)
        team_ids = self.env['crm.team'].get_team_ids_by_branches(branch_ids)
        return [('id', 'in', team_ids)]

    name = fields.Char(string='Keyword', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string="Partner", track_visibility='onchange')
    name_of_lead = fields.Char(string='Name of Lead', track_visibility='onchange')
    phone_number = fields.Char(string='Phone number', track_visibility='onchange')
    partner_mobile = fields.Char(string='Mobile number', track_visibility='onchange')
    partner_name = fields.Char(string="Partner name", track_visibility='onchange')
    partner_code = fields.Char(string="Partner code", track_visibility='onchange')
    partner_user_id = fields.Many2one('res.users', related='partner_id.user_id', string='Partner user', readonly=True,
                                      store=True, track_visibility='onchange')
    partner_team_id = fields.Many2one('crm.team', related='partner_id.x_crm_team_id', string='Partner team',
                                      readonly=True,
                                      store=True, track_visibility='onchange')
    partner_stage_id = fields.Many2one('crm.stage', related='partner_id.x_stage_id', string='Partner stage',
                                       readonly=True, store=True, track_visibility='onchange')
    country_id = fields.Many2one('res.country', string="Country", default=_default_country_id,
                                 track_visibility='onchange')
    state_id = fields.Many2one('res.country.state', string="Province", track_visibility='onchange')
    district_id = fields.Many2one('res.district', string="District", track_visibility='onchange')
    level_age_id = fields.Many2one('level.age', string='Level Age', track_visibility='onchange')
    partner_status_ids = fields.Many2many('partner.status', string="Partner status", track_visibility='onchange')
    address = fields.Char(string="Address", track_visibility='onchange')
    birthday = fields.Date(string="Birthday", track_visibility='onchange')
    email = fields.Char(string="Email", track_visibility='onchange')

    booking_id = fields.Many2one('service.booking', string="Booking", track_visibility='onchange')
    booking_team_id = fields.Many2one('crm.team', related='booking_id.team_id', string="Booking team", readonly=True,
                                      store=True, track_visibility='onchange')
    booking_user_id = fields.Many2one('res.users', related='booking_id.user_id', string="Booking user", readonly=True,
                                      store=True, track_visibility='onchange')
    booking_type = fields.Selection(related='booking_id.type', string="Booking type", readonly=True, store=True)
    booking_date = fields.Date(related='booking_id.date', string='Booking date', readonly=True, store=True,
                               track_visibility='onchange')
    booking_period_id = fields.Many2one('booking.period', related='booking_id.booking_period_id',
                                        string='Booking period', readonly=True, store=True, track_visibility='onchange')

    # booking_time_from = fields.Datetime(related='booking_id.time_from', string="Booking time from", readonly=True,
    #                                     store=True, track_visibility='onchange')
    booking_categ_id = fields.Many2one('product.category', related='booking_id.categ_id', string="Booking category",
                                       readonly=True, store=True, track_visibility='onchange')

    lead_ids = fields.Many2many('crm.lead', string="Leads", track_visibility='onchange')
    count_lead = fields.Integer(string="Count lead", track_visibility='onchange')
    search_result = fields.Selection(
        [('not_search', 'Not search'), ('not_found', 'Not Found'), ('found_one', 'Found one'),
         ('found_many', 'Found many')], default="not_search", string="Search result", track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='User', track_visibility='onchange')
    team_id = fields.Many2one('crm.team', string='Team', default=_default_team_id, domain=_domain_team_id,
                              track_visibility='onchange')
    campaign_id = fields.Many2one('utm.campaign', string="Campaign", track_visibility='onchange')
    date_meeting = fields.Datetime(string='Date', track_visibility='onchange')
    note = fields.Text(string='Note', track_visibility='onchange')
    state = fields.Selection([('new', 'New'), ('assigned', 'Assigned'), ('done', 'Done')], default='new',
                             string='State', track_visibility='onchange')
    booking_note = fields.Text(string='Booking note', related='booking_id.note', readonly=True, store=True,
                               track_visibility='onchange')

    @api.multi
    def action_search(self):
        if not self.name: raise UserError("Bạn chưa nhập từ khóa!")
        if self.state != 'new': raise UserError(
            "Bản ghi đã thay đổi trạng thái, vui lòng tải lại trang để cập nhật trạng thái mới nhất!")
        keyword = str(self.name).strip()
        partner = self.env['res.partner'].search(
            ['|', '|', '|', '|', ('phone', '=', keyword), ('mobile', '=', keyword), ('x_mobile2', '=', keyword),
             ('x_code', '=', keyword), ('x_old_code', '=', keyword)], limit=1).with_context({'reception_customer': True})
        # partner = self.env['res.partner'].search([]).with_context({'reception_customer': True})
        if partner:
            booking = self.env['service.booking'].search([('customer_id', '=', partner.id), ('state', '=', 'ready')],
                                                         limit=1)
            user_id = self._uid
            if not booking:
                user_id = partner.user_id.id
            elif booking.type == 'meeting':
                user_id = booking.user_id.id
            elif booking.type == 'service':
                user_id = partner.user_id.id
            else:
                raise UserError(
                    "Có lỗi xảy ra, liên hệ Admin để được giải quyết! booking_type: %s" % (str(booking.type)))
            self.write({
                'partner_id': partner.id,
                'phone_number': partner.phone,
                'partner_mobile': partner.mobile,
                'partner_name': partner.name,
                'partner_code': partner.x_code,
                'partner_status_ids': [(6, 0, partner.x_partner_status_ids.ids)],
                'state_id': partner.state_id.id,
                'district_id': partner.x_district_id.id,
                'level_age_id': partner.x_level_age_id.id,
                'address': partner.street,
                'birthday': partner.x_birthday,
                'email': partner.email,
                'booking_id': booking and booking.id or False,
                'search_result': 'found_one',
                'user_id': user_id,
            })
        else:
            phone_number = False
            if keyword.replace(' ', '').isdigit():
                phone_number = keyword.replace(' ', '')
            self.write(
                {'partner_id': False, 'phone_number': phone_number, 'partner_mobile': False, 'partner_name': False,
                 'partner_code': False, 'partner_status_ids': [(6, 0, [])], 'state_id': False, 'district_id': False,
                 'level_age_id': False,
                 'address': False, 'birthday': False, 'email': False, 'booking_id': False,
                 'search_result': 'not_found', })

    @api.multi
    def action_create(self):
        if self.state != 'new': raise UserError(
            "Bản ghi đã thay đổi trạng thái, vui lòng tải lại trang để cập nhật trạng thái mới nhất!")
        phone_number = False
        if self.name and self.name.replace(' ', '').isdigit():
            phone_number = self.name.replace(' ', '')
        self.write({'partner_id': False, 'phone_number': phone_number, 'partner_mobile': False, 'partner_name': False,
                    'partner_code': False, 'partner_status_ids': [(6, 0, [])], 'state_id': False, 'district_id': False,
                    'level_age_id': False,
                    'address': False, 'birthday': False, 'email': False, 'booking_id': False,
                    'search_result': 'not_search', })

    @api.multi
    def action_assign(self):
        if self.state == 'new':
            if not self.user_id: raise UserError("Bạn phải chọn người tiếp đón!")
            if not self.team_id: raise UserError("Bạn phải chọn cơ sở tiếp đón!")

            self.state = 'assigned'

            if not self.partner_id:
                if not self.team_id.x_branch_id: UserError(
                    "Cơ sở tiếp đón %s chưa chọn chi nhánh" % (str(self.team_id.name)))
                if not self.team_id.x_branch_id.brand_id: UserError(
                    "Chi nhánh %s của cơ sở tiếp đón %s chưa chọn thương hiệu" % (
                        str(self.team_id.x_branch_id.name), str(self.team_id.name)))
                if not self.phone_number: raise UserError("Bạn phải nhập số điện thoại của khách hàng")
                if not self.partner_name: raise UserError("Bạn phải nhập tên của khách hàng")
                partner_by_phone_number = self.env['res.partner'].search(
                    ['|', ('phone', '=', self.phone_number), ('mobile', '=', self.phone_number)])
                if partner_by_phone_number: raise UserError(
                    "Đã tồn tại khách hàng sử dụng số điện thoại %s. Vui lòng kiểm tra lại!" % (str(self.phone_number)))
                if self.partner_mobile:
                    partner_by_partner_mobile = self.env['res.partner'].search(
                        ['|', ('phone', '=', self.partner_mobile), ('mobile', '=', self.partner_mobile)])
                    if partner_by_partner_mobile: raise UserError(
                        "Đã tồn tại khách hàng sử dụng số di động %s. Vui lòng kiểm tra lại!" % (
                            str(self.partner_mobile)))
                stage_opportunity = self.env['crm.stage'].search([('x_code', '=', 'opportunity')], limit=1)
                if not stage_opportunity: UserError("Không tìm thấy trạng thái khách hàng có mã: opportunity")
                partner = self.env['res.partner'].create({
                    'name': self.partner_name,
                    'x_partner_status_ids': [(6, 0, self.partner_status_ids.ids)],
                    'phone': self.phone_number,
                    'mobile': self.partner_mobile,
                    'x_brand_id': self.team_id.x_branch_id.brand_id.id,
                    # 'user_id': self.user_id.id,
                    # 'x_crm_team_id': self.team_id.id,
                    'state_id': self.state_id and self.state_id.id or False,
                    'x_district_id': self.district_id and self.district_id.id or False,
                    'street': self.address,
                    'x_birthday': self.birthday,
                    'x_stage_id': stage_opportunity.id,
                    'customer': True,
                })
                self.partner_id = partner.id
            else:
                if self.booking_id:
                    self.booking_id.action_met()
        elif self.state == 'assigned':
            view_id = self.env.ref('izi_pos_crm.reception_customer_assign_form_view').id
            ctx = self._context.copy()
            return {
                'name': 'Giao lead',
                'type': 'ir.actions.act_window',
                'res_model': 'reception.customer',
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(view_id, 'form')],
                'target': 'new',
                'context': ctx,
            }
        else:
            raise UserError("Bản ghi đã thay đổi trạng thái, vui lòng tải lại trang để cập nhật trạng thái mới nhất!")

    @api.multi
    def action_confirm(self):
        if self.state != 'assigned':
            raise UserError("Bản ghi đã thay đổi trạng thái, vui lòng tải lại trang để cập nhật trạng thái mới nhất!")
        return True

    @api.multi
    def action_confirm_reception(self):
        for s in self:
            if s.state != 'assigned':
                raise UserError("Bản ghi đã thay đổi trạng thái, vui lòng tải lại trang để cập nhật trạng thái mới nhất!")
            if not s.partner_id.user_id or not s.partner_id.x_crm_team_id:
                s.partner_id.user_id = s.user_id.id
                s.partner_id.x_crm_team_id = s.team_id.id
            s.state = 'done'
