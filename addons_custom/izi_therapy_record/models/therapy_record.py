# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError, MissingError, except_orm
import time
from odoo import http
import logging

_logger = logging.getLogger(__name__)


class TherapyRecord(models.Model):
    _name = 'therapy.record'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Partner', track_visibility='onchange')
    partner_code = fields.Char(string='Code', related='partner_id.x_code', readonly=True)
    partner_user_id = fields.Many2one('res.users', related='partner_id.user_id', readonly='True', string='Salesperson')
    partner_birthday = fields.Date(string='Birthday', related='partner_id.x_birthday', readonly=True)
    partner_level_age_id = fields.Many2one('level.age', related='partner_id.x_level_age_id', string='Level Age',
                                           readonly=True)
    partner_street = fields.Char(string='Street', related='partner_id.street', readonly=True)
    partner_state_id = fields.Many2one('res.country.state', string='State', related='partner_id.state_id',
                                       readonly=True)
    partner_country_id = fields.Many2one('res.country', string='Country', related='partner_id.country_id',
                                         readonly=True)
    partner_phone = fields.Char(string='Phone', related='partner_id.phone', readonly=True, store=True)
    crm_lead_tag_ids = fields.Many2many('crm.lead.tag', string='Tag', related='partner_id.x_crm_lead_tag_ids',
                                        readonly=True)
    user_id = fields.Many2one('res.users', string='User', track_visibility='onchange')
    categ_id = fields.Many2one('product.category', string='Category', track_visibility='onchange')
    note = fields.Text('Warning Information')  # thông tin lưu ý
    therapy_body_measure_ids = fields.One2many('therapy.body.measure', 'therapy_record_id', 'Therapy body measure')
    therapy_prescription_ids = fields.One2many('therapy.prescription', 'therapy_record_id',
                                               string='Therapy prescription')  # phiếu chỉ định
    therapy_record_product_ids = fields.One2many('therapy.record.product', 'therapy_record_id',
                                                 string='Therapy record product')  # tổng sản phẩm, dịch vụ tồn
    therapy_record_update_product_ids = fields.One2many('therapy.record.product.update', 'therapy_record_id',
                                                 string='Therapy record product update')  # lsử cập nhật sản phẩm, dịch vụ tồn
    therapy_prescription_return_product_line_ids = fields.One2many('therapy.prescription.return.product.line',
                                                                   'therapy_record_id',
                                                                   string='Therapy Prescription Return Product')
    is_inventory = fields.Boolean(string='Is Inventory', default=False)
    state = fields.Selection(
        [('in_therapy', 'In Therapy'), ('signed_commitment', 'Signed Committed'), ('stop_care', 'Stop Care'),
         ('cancel', 'Cancel')], default="in_therapy", string='State', track_visibility='onchange')
    stock_picking_ids = fields.One2many('stock.picking', 'x_therapy_record_id', string='Picking return')
    conpute_id = fields.Float(compute='_compute_id', string="Compute View")

    def _compute_id(self):
        cr = self._cr
        for record in self:
            record.conpute_id = record.id

    @api.constrains('state', 'partner_id', 'categ_id')
    def _constrains_state_partner_id_categ_id(self):
        for s in self:
            exist_therapy_record = self.search([('state', 'not in', ['stop_care', 'cancel']), ('partner_id', '=', s.partner_id.id), ('categ_id', '=', s.categ_id.id), ('id', '!=', s.id)])
            if exist_therapy_record:
                raise ValidationError('Đã tồn tại một Hồ sơ trị liệu của khách hàng %s có nhóm dịch vụ là %s' %(exist_therapy_record.partner_id.name, exist_therapy_record.categ_id.name))

    @api.model
    def default_get(self, fields):
        res = super(TherapyRecord, self).default_get(fields)
        res['user_id'] = self._context.get('uid')
        return res

    def create_prescription(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.update({
            'default_therapy_record_id': self.id,
            'default_user_id': self.env.uid
        })
        view = self.env.ref('izi_therapy_record.izi_view_therapy_prescription_form')
        return {
            'name': _('Therapy Prescription'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'therapy.prescription',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            'context': ctx,
        }

    def action_sign_commitment(self):
        if self.state != 'in_therapy':
            raise UserError("Bản ghi đã thay đổi trạng thái, vui lòng tải lại trang để cập nhật trạng thái mới nhất!")
        self.state = 'signed_commitment'

    def action_stop_care(self):
        if self.state not in ['signed_commitment', 'in_therapy']:
            raise UserError("Bản ghi đã thay đổi trạng thái, vui lòng tải lại trang để cập nhật trạng thái mới nhất!")
        self.state = 'stop_care'

    def action_show_view_update_product(self):
        view_id = self.env.ref('izi_therapy_record.therapy_record_product_update_form_popup_view').id
        ctx = {
            'default_therapy_record_id': self.id,
            'default_user_id': self._uid,
        }
        return {
            'name': 'Therapy Record Product Update',
            'type': 'ir.actions.act_window',
            'res_model': 'therapy.record.product.update',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': ctx,
        }

    def action_back_state(self):
        if self.state == 'stop_care':
            therapy_id = self.env['therapy.record'].search([('partner_id', '=', self.partner_id.id), ('categ_id', '=', self.categ_id.id), ('state', 'in', ['signed_commitment', 'in_therapy'])])
            if therapy_id:
                raise UserError('Đã tồn tại một hồ sơ trị liệu có trạng thái ký đạt cam kết hoặc trong liệu trình của khách hàng %s có nhóm dịch vụ là %s' % (self.partner_id.name, self.categ_id.name))
            self.state = 'signed_commitment'
        elif self.state == 'signed_commitment':
            self.state = 'in_therapy'
        else:
            pass

    # Trả hàng
    @api.multi
    def action_return_product(self):
        for picking in self.stock_picking_ids.filtered(lambda picking:picking.picking_type_id.code == 'incoming'):
            if picking.state != 'done':
                raise ValidationError(
                    'Đơn nhập kho %s chưa được hoàn thành.Vui lòng kiểm tra lại' % picking.name)
        if self.state != 'in_therapy':
            raise except_orm('Cảnh báo!',
                             ("Hồ sơ trị liệu không ở trạng thái trong liệu trình, vui lòng kiểm tra lại để cập nhật"))
        ctx = {
            'default_partner_id': self.partner_id.id,
            'default_therapy_record_id': self.id,
            'default_user_id': self.env.uid,
        }
        view = self.env.ref('izi_therapy_record.izi_view_therapy_prescription_return_product_popup')
        return {
            'name': 'Trả hàng',
            'type': 'ir.actions.act_window',
            'res_model': 'therapy.prescription.return.product',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            # 'res_id': self.id,
            'context': ctx
        }

    @api.model
    def get_measure_body_detail_therapy_record(self, therapy_id):
        measure_line_details = []
        body_ids = []
        arr_body = []
        time_measure = []
        body = []
        # if categ_id:
        therapy_measure_ids = self.env['therapy.body.measure'].sudo().search([('therapy_record_id', '=', therapy_id)], order="measurement_time desc")
        if therapy_measure_ids:
            for therapy_measure_id in therapy_measure_ids:
                vals = {
                    'measurement':  (datetime.strptime(therapy_measure_id.measurement_time,"%Y-%m-%d %H:%M:%S") + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S") ,
                    'product_id': therapy_measure_id.product_id.name,
                    'body': body,
                }
                for measure_line_id in sorted((therapy_measure_id.body_measure_line_ids), key=lambda r: r.body_area_id.name):
                    if measure_line_id.body_area_id.code not in arr_body and measure_line_id.body_area_id.code != False:
                        arr_body.append(measure_line_id.body_area_id.code)
                        body_ids.append({
                            'name': measure_line_id.body_area_id.name,
                            'code': measure_line_id.body_area_id.code
                        })
                    body.append({
                        'body_area_code': measure_line_id.body_area_id.code,
                        'measurement': measure_line_id.measurement,
                    }),
                measure_line_details.append(vals)
                body = []

        return measure_line_details, body_ids

    def _read_from_database(self, field_names, inherited_field_names=[]):
        super(TherapyRecord, self)._read_from_database(field_names, inherited_field_names)
        context = self._context
        if 'partner_phone' in field_names:
            for record in self:
                try:
                    UserObj = http.request.env['res.users']
                    display_phone = UserObj.has_group('izi_display_fields.group_display_phone')
                    if display_phone or self.env.uid == 1:
                        record._cache['partner_phone']
                    else:
                        # record._cache['phone']
                        record._cache['partner_phone'] = record._cache['partner_phone'][0:len(record._cache['partner_phone']) - 3] + '***'
                except Exception:
                    pass

    # @api.multi
    # def read(self, fields=None, load='_classic_read'):
    #     result = super(TherapyRecord, self).read()
    #     for record in result:
    #         if record['partner_phone']:
    #             try:
    #                 UserObj = http.request.env['res.users']
    #                 display_phone = UserObj.has_group('izi_display_fields.group_display_phone')
    #                 if display_phone or self.env.uid == 1:
    #                     record['partner_phone'] = record['partner_phone'][0:len(record['partner_phone']) - 3] + '***'
    #                 else:
    #                     record['partner_phone'] = record['partner_phone'][0:len(record['partner_phone']) - 3] + '***'
    #             except Exception:
    #                 pass
    #     return result

    @api.model
    def create(self, vals):
        if not vals.get('name') and vals.get('categ_id') and vals.get('partner_id'):
            categ_id = self.env['product.category'].search([('id', '=', vals.get('categ_id'))])
            partner_id = self.env['res.partner'].search([('id', '=', vals.get('partner_id'))])
            if categ_id and partner_id:
                vals['name'] = categ_id and f'{partner_id.name} - {categ_id.name}' or ''
        # if vals['partner_id'] and vals['categ_id']:
        #     therapy_id = self.env['therapy.record'].search([('partner_id', '=', vals['partner_id']), ('categ_id', '=', vals['categ_id']), ('state', 'not in', ['stop_care', 'cancel'])], limit=1)
        #     if therapy_id:
        #         raise UserError('Đã tồn tại một Hồ sơ trị liệu của khách hàng %s có nhóm dịch vụ là %s' %(therapy_id.partner_id.name, therapy_id.categ_id.name))
        return super(TherapyRecord, self).create(vals)


    @api.multi
    def unlink(self):
        for therapy in self:
            check = True
            for therapy_product in  therapy.therapy_record_product_ids:
                if therapy_product.qty_max == 0:
                    check = False
            if check:
                raise UserError('Hồ sơ trị liệu của khách hàng %s vẫn còn sản phẩm dịch vụ tồn! Vui lòng sử dụng hết sản phẩm tồn trước khi xóa Hồ sơ trị liệu.' %(therapy.partner_id.name))
        return super(TherapyRecord, self).unlink()