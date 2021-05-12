
from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
import datetime

_logger = logging.getLogger(__name__)


class ServiceBooking(models.Model):
    _name = 'service.booking'
    _description = 'Service booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date DESC'

    name = fields.Char(string='Name', track_visibility='onchange')
    type = fields.Selection([('service', 'Service Booking'), ('meeting', 'Customer meeting')],
                            default='service', track_visibility='onchange')
    customer_id = fields.Many2one('res.partner', string="Customer", track_visibility='onchange')
    lead_id = fields.Many2one('crm.lead', string="Lead", track_visibility='onchange')
    date = fields.Date(string="Date", track_visibility='onchange', copy=False)
    # time_from = fields.Datetime(string="Time From", track_visibility='onchange', copy=False)
    services = fields.Many2many('product.product', string="Services", domain=[('product_tmpl_id.type', '=', 'service')])
    state = fields.Selection([('ready', 'Ready'), ('met', 'Met'), ('cancel', 'Cancel')], default='ready', track_visibility='onchange')
    team_id = fields.Many2one('crm.team', string='Team', track_visibility='onchange')
    user_id = fields.Many2one('res.users', string="User", track_visibility='onchange')
    categ_id = fields.Many2one('product.category', string="Product category", track_visibility='onchange')
    partner_status_ids = fields.Many2many('partner.status', string="Partner status", track_visibility='onchange')
    note = fields.Text(string='Note')
    booking_period_id = fields.Many2one('booking.period', string='Booking period', compute='compute_booking_period', store=True)

    # @api.depends('time_from')
    # def compute_booking_period(self):
    #     for detail in self:
    #         if detail.time_from:
    #             time_from = datetime.datetime.strptime(detail.time_from, '%Y-%m-%d %H:%M:%S')
    #             time_from_cvt_tz = time_from + timedelta(hours=7)
    #             time_from_hour = time_from_cvt_tz.hour + time_from_cvt_tz.minute / 60
    #             booking_period = self.env['booking.period'].search(
    #                 [('from_time', '<=', time_from_hour), ('to_time', '>=', time_from_hour)], limit=1)
    #             if not booking_period:
    #                 raise except_orm('Cảnh báo!', ('Không tìm thấy khung giờ phù hợp với khoảng thời gian vừa chọn. Vui lòng kiểm tra lại.'))
    #             detail.booking_period_id = booking_period.id

    # @api.onchange('time_from')
    # def _onchange_date(self):
    #     for detail in self:
    #         if detail.time_from:
    #             time_from = datetime.datetime.strptime(detail.time_from, '%Y-%m-%d %H:%M:%S')
    #             detail.date = time_from.date()

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'ready':
                raise except_orm('Cảnh báo!', ('Không thể xóa bản ghi ở trạng thái khác sẵn sàng'))
        super(ServiceBooking, self).unlink()

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if not self.customer_id:
            return {'value': {'partner_status_ids': [(6, 0, self.customer_id.x_partner_status_ids.ids)]}}
        else:
            return {'value': {'partner_status_ids': [(6, 0, self.customer_id.x_partner_status_ids.ids)]}}

    @api.constrains('customer_id', 'partner_status_ids')
    def _check_customer_id_partner_status_ids(self):
        if self.customer_id and self.partner_status_ids:
            self.customer_id.x_partner_status_ids = self.partner_status_ids
            # self.customer_id.partner_status_ids = [(6, 0, self.partner_status_ids.ids)]

    @api.model
    def create(self, vals):
        if not vals.get('name', False):
            vals['name'] = self.get_service_booking_name(vals.get('type', 'service'))
        if vals.get('customer_id') != None:
            booking_obj = self.env['service.booking'].search([('state', '=', 'ready'), ('customer_id', '=', vals.get('customer_id'))], limit=1)
            if (booking_obj):
                raise except_orm('Cảnh báo!', ("Khách hàng %s đang có 1 Booking/Meeting ở trạng thái sẵn sàng" % booking_obj.customer_id.name))
            # if vals.get('partner_status_ids') != None and vals.get('partner_status_ids'):
            #     self.customer_id.partner_status_ids = vals.get('partner_status_ids')
        booking = super(ServiceBooking, self).create(vals)
        return booking

    def get_service_booking_name(self, type):
        seq = 'ev_service_meeting_name_seq'
        if type == 'service':
            seq = 'ev_service_booking_name_seq'
        return self.env['ir.sequence'].with_context(**self._context).next_by_code(seq)

    @api.multi
    def action_confirm(self):
        self.write({'state': 'met'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.multi
    def action_met(self):
        self.write({'state': 'met'})


