# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, except_orm
import logging

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # x_state = fields.Selection([('lead', 'Lead'), ('reference', 'Reference'), ('reference2', 'Reference2'),
    #                             ('opportunity', 'Opportunity'),
    #                             ('meeting', 'Meeting'),
    #                             ('to_shop', 'To shop'),
    #                             ('confirm', 'Confirm'),
    #                             ('won', 'Won'),
    #                             ('lose', 'Lose')], default="lead", string="State")
    service_booking_ids = fields.One2many('service.booking', 'lead_id', string="Service Booking")
    service_booking_count = fields.Integer(string='Delivery Orders', compute='_compute_service_booking_ids')
    # time_booking = fields.Datetime(string='Time Booking', compute='get_time_booking')

    # @api.depends('service_booking_ids')
    # def get_time_booking(self):
    #     for s in self:
    #         have_booking = False
    #         for service_booking in s.service_booking_ids:
    #             if service_booking.state == 'ready':
    #                 s.time_booking = service_booking.time_from
    #                 have_booking = True
    #                 break
    #             elif service_booking.state == 'met':
    #                 s.time_booking = service_booking.time_from
    #                 have_booking = True
    #                 break
    #         if not have_booking: s.time_booking = False

    @api.multi
    def action_view_service_booking(self):
        action = self.env.ref('izi_crm_booking.action_service_booking').read()[0]

        service_bookings = self.mapped('service_booking_ids')
        if len(service_bookings) > 1:
            action['domain'] = [('id', 'in', service_bookings.ids)]
        elif service_bookings:
            action['views'] = [(self.env.ref('izi_crm_booking.service_booking_form_view').id, 'form')]
            action['res_id'] = service_bookings.id
        return action

    @api.depends('service_booking_ids')
    def _compute_service_booking_ids(self):
        for lead in self:
            lead.service_booking_count = len(lead.service_booking_ids)

    @api.multi
    def action_booking(self):
        return self.__get_view('service')

    @api.multi
    def action_meeting(self):
        return self.__get_view('meeting')

    def __get_view(self, type):
        view_id = self.env.ref('izi_crm_booking.service_booking_form_view').id
        if not self.partner_id:
            vals = {
                'name': self.partner_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'country_id': self.country_id.id,
                'email': self.email_from,
                'phone': self.phone,
                'mobile': self.mobile,
                'zip': self.zip,
                'website': self.website,
                'customer': True,
                'x_birthday': self.x_birthday,
                'type': '',
                'x_manage_user_id': self.user_id.id,
                'x_crm_team_id': self.team_id.id,
                'x_brand_id': self.team_id.x_branch_id.brand_id.id,
            }
            partner_id = self.env['res.partner'].create(vals)
            self.partner_id = partner_id.id

        products = self.__get_service_booking_products()

        ctx = {
            'default_crm_lead_id': self.id,
            'default_type': type,
            'default_customer_id': self.partner_id.id,
            'default_product_ids': products,
            'default_team_id': self.team_id.id if self.team_id else False,
            'default_user_id': self.user_id.id if self.user_id else False,
        }
        return {
            'name': type[0].upper() + type[1:],
            'type': 'ir.actions.act_window',
            'res_model': 'service.booking',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'context': ctx,
        }

    def __get_service_booking_products(self):
        if not self.x_lines:
            return []

        products = [(0, 0, {'product_id': line.product_id.id,
                            'qty': line.qty,
                            'amount_total': line.total_amount})
                    for line in self.x_lines]
        return products

    @api.multi
    def action_create_bk_mt(self):
        if not self.team_id:
            raise except_orm('Cảnh báo!', ("Bạn chưa chọn nhóm bán hàng!"))

        count = 0
        for i in self.service_booking_ids:
            if i.state == 'ready':
                count += 1
            if count > 0:
                raise ValidationError('Đang có 1 Booking/Meeting ở trạng thái sẵn sàng.Vui lòng kiểm tra lại!')
        view = self.env.ref('izi_crm_booking.service_booking_form_view_1')
        ctx = {
            'default_customer_id': self.partner_id.id,
            'default_lead_id': self.id,
        }

        return {
            'name': ('Booking/Meeting'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'service.booking',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            # 'res_id': self.interaction_ids.id,
            'context': ctx,
        }

    # @api.multi
    # def write(self, vals):
    #     lead = super(CrmLead, self).write(vals)
    #     context = self._context
    #     _logger.error("ngadv context: %s" % (str(context)))
    #     if self.x_state == 'meeting' and not context['interaction_meeting_create_lead']:
    #         check = False
    #         for service_booking in self.service_booking_ids:
    #             if service_booking.state == 'ready':
    #                 check = True
    #         if not check:
    #             raise ValidationError('Vui lòng đặt hẹn cho lead trước khi chuyển trạng thái!')
    #     return lead