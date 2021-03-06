# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import except_orm, ValidationError, UserError
from odoo.osv import expression
from odoo import sys, os
import base64, time
from os.path import join
from datetime import datetime, date
import logging, re
from odoo import http
from lxml import etree
from odoo.osv.orm import setup_modifiers
from dateutil.relativedelta import relativedelta

# source_folder_path = os.path.dirname(__file__)
# index_folder_path = source_folder_path.find('dev')
# if source_folder_path[index_folder_path - 1] != '\\' and source_folder_path[index_folder_path - 1] != '/':
#     folder_path = source_folder_path[:index_folder_path] + '/filestore_dir/partner_files'
# else:
#     folder_path = source_folder_path[:index_folder_path] + 'filestore_dir/partner_files'
# if not os.path.exists(folder_path):
#     os.mkdir(folder_path)
# folder_path = '/data/filestore_dir/partner_files' + '/' #server

folder_root = 'odoo'
folder_filestore = '/filestore_dir/partner_files'
folder_path = os.path.dirname(__file__)[:(os.path.dirname(__file__).find(folder_root) + len(folder_root))]
NUMBER_SEQUENCE = 1

_logger = logging.getLogger(__name__)


class ResPartnerCustom(models.Model):
    _inherit = 'res.partner'

    def _default_country_id(self):
        country = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
        if not country:
            raise UserError("Chưa có quốc gia Việt Nam, vui lòng liên hệ Admin")
        return country.id

    x_brand_id = fields.Many2one("res.brand", "Brand")

    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'), ('company', 'Company')],
                                    compute='_compute_company_type', inverse='_write_company_type')
    user_id = fields.Many2one('res.users', string='Salesperson', help='The internal user that is in charge of communicating with this contact if any.', track_visibility='onchange')
    x_presenter = fields.Many2one('res.partner', 'Presenter', track_visibility='onchange', )  # Người giới thiệu
    x_old_code = fields.Char(string="Partner old code", copy=False, track_visibility='onchange')
    x_code = fields.Char(string="Partner code", copy=False, track_visibility='onchange')
    x_manage_user_id = fields.Many2one('res.users', "Manage User",
                                       track_visibility='onchange')  # Nhân viên phụ trách với khách hàng này
    x_revenue_old = fields.Float("Revenue Old", track_visibility='onchange')  # Doanh thu cũ
    x_profile_customer_ids = fields.One2many('izi.images.profile.customer', 'partner_id', "Profile Customer")
    x_images = fields.Many2many(comodel_name="ir.attachment", relation="m2m_res_partner_ir_attachment_relation",
                                column1="partner_id",
                                column2="attachment_id", string="Attachments", )
    # x_code_update = fields.Char('Code Update')
    x_crm_team_id = fields.Many2one("crm.team", "Crm Team", track_visibility='onchange')
    source_id = fields.Many2one('utm.source', "Source", track_visibility='onchange')
    x_sex = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], string="Sex", track_visibility='onchange')
    x_crm_lead_tag_ids = fields.Many2many('crm.lead.tag', string="Tag", track_visibility='onchange')
    x_link_facebook = fields.Char(string="Link facebook", track_visibility='onchange')
    x_link_zalo = fields.Char(string="Link zalo", track_visibility='onchange')
    x_district_id = fields.Many2one('res.district', string="District", track_visibility='onchange')
    x_visiting_last = fields.Date(string='The last visiting', track_visibility='onchange')
    x_birthday = fields.Date(string='Birthday', track_visibility='onchange')
    x_level_age_id = fields.Many2one('level.age', string='Level Age', compute='get_level_age', track_visibility='onchange')
    x_age = fields.Integer(string='Age', compute='get_level_age', track_visibility='onchange')
    x_category_ids = fields.Many2many('product.category', string='Category', track_visibility='onchange')
    x_telesales_id = fields.Many2one('res.users', string='Telesales', track_visibility='onchange')
    x_last_interaction = fields.Date(string='Last Interaction', track_visibility='onchange')
    x_presenter_phone = fields.Char(string='Presenter Phone', track_visibility='onchange')
    x_enclosed_phone = fields.Char(string='Enclosed Phone', track_visibility='onchange')
    x_partner_job = fields.Char(string='Partner Job', track_visibility='onchange')
    x_next_interaction_reminder_date = fields.Date(string='Next interaction reminder date', track_visibility='onchange')
    x_next_interaction_reminder_activity_type_id = fields.Many2one('mail.activity.type', string='Next interaction reminder activity', track_visibility='onchange')
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', track_visibility='onchange')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=_default_country_id, track_visibility='onchange')

    x_mobile2 = fields.Char(string="Mobile 2", track_visibility='onchange')

    _sql_constraints = [
        ('x_code_uniq', 'unique(x_code)', 'Partner Code is unique'),
        ('x_old_code_uniq', 'unique(x_old_code)', 'Partner old code is unique'),
        ('phone_brand_uniq', 'unique(phone, x_brand_id)', 'Partner phone is unique in a brand'),
        ('mobile_brand_uniq', 'unique(mobile, x_brand_id)', 'Partner mobile is unique in a brand'),
        ('x_mobile2_brand_uniq', 'unique(x_mobile2, x_brand_id)', 'Partner mobile 2 is unique in a brand'),
    ]

    # _sql_constraints = [
    #     ('phone_brand_uniq', 'unique(phone, x_brand_id)', 'Partner phone is unique in a brand'),
    #     ('mobile_brand_uniq', 'unique(mobile, x_brand_id)', 'Partner mobile is unique in a brand'),
    # ]

    @api.onchange('state_id')
    def _onchange_state_id(self):
        return {'value': {'x_district_id': False}}

    @api.model
    def create(self, vals):
        if vals.get('phone'):
            partner_id = self.env['res.partner'].search(
                ['|', '|', ('phone', '=', vals.get('phone').strip()), ('mobile', '=', vals.get('phone').strip()), ('x_mobile2', '=', vals.get('phone').strip())], limit=1)
            if len(partner_id) != 0 and partner_id.x_brand_id.id == vals.get('x_brand_id'):
                raise except_orm('Cảnh báo!',
                                 _("Tồn tại khách hàng có số điện thoại này: %s" % (str(vals.get('phone')))))
        if vals.get('mobile'):
            partner_id = self.env['res.partner'].search(
                ['|', '|', ('phone', '=', vals.get('mobile').strip()), ('mobile', '=', vals.get('mobile').strip()), ('x_mobile2', '=', vals.get('mobile').strip())], limit=1)
            if len(partner_id) != 0 and partner_id.x_brand_id.id == vals.get('x_brand_id'):
                raise except_orm('Cảnh báo!',
                                 _("Tồn tại khách hàng có số di động này: %s" % (str(vals.get('mobile')))))
        if vals.get('x_mobile2'):
            partner_id = self.env['res.partner'].search(
                ['|', '|', ('phone', '=', vals.get('mobile').strip()), ('mobile', '=', vals.get('mobile').strip()), ('x_mobile2', '=', vals.get('x_mobile2').strip())], limit=1)
            if len(partner_id) != 0 and partner_id.x_brand_id.id == vals.get('x_brand_id'):
                raise except_orm('Cảnh báo!',
                                 _("Tồn tại khách hàng có số di động này: %s" % (str(vals.get('x_mobile2')))))
        partner = super(ResPartnerCustom, self).create(vals)
        if partner.x_code:
            partner.x_code = partner.x_code.strip().upper()
        else:
            SequenceObj = self.env['ir.sequence']
            context = {'force_company': 1}
            if partner.is_company:
                sequence_generate = SequenceObj.with_context(**context).next_by_code('company_code')
                code_sequence = 'company_code'
            elif partner.supplier:
                sequence_generate = SequenceObj.with_context(**context).next_by_code('supplier_code')
                code_sequence = 'supplier_code'
            elif partner.customer:
                #mã KH sẽ tạo khi chuyển KH sang trạng thái chốt
                if partner.x_stage_id.x_code == 'won':
                    if not partner.x_crm_team_id: raise UserError("Khách hàng có số điện thoại %s chưa chọn cơ sở làm dịch vụ" % (str(partner.phone)))
                    if not partner.x_crm_team_id.x_branch_id: raise UserError("Cơ sở làm dịch vụ %s chưa chọn chi nhánh" % (str(partner.x_crm_team_id.name)))
                    sequence_generate = self._generate_customer_code(partner.x_crm_team_id.x_branch_id.code).strip().upper()
                else:
                    return partner
            else:
                sequence_generate = SequenceObj.with_context(**context).next_by_code('user_code')
                code_sequence = 'user_code'
            if not sequence_generate:
                raise except_orm('Thông báo', 'Không tìm thấy Trình tự sinh mã đối tác có mã: %s' % (code_sequence,))
            partner.x_code = sequence_generate.strip().upper()
        if partner.x_old_code:
            partner.x_old_code = partner.x_old_code.strip().upper()
        else:
            partner.x_old_code = partner.x_code
        return partner

    @api.multi
    def write(self, vals):
        if 'phone' in vals and vals['phone']:
            partner_id = self.env['res.partner'].search(
                ['|', '|', ('phone', '=', vals.get("phone")), ('mobile', '=', vals.get("phone")), ('x_mobile2', '=', vals.get("phone")),
                 ('id', '!=', self.id)])
            if partner_id and partner_id.x_brand_id.id == self.x_brand_id.id:
                raise except_orm('Cảnh báo!', _("Tồn tại khách hàng có số điện thoại này"))
        if 'mobile' in vals and vals['mobile']:
            if vals.get("mobile"):
                partner_id = self.env['res.partner'].search(
                    ['|', '|', ('phone', '=', vals.get("mobile")), ('mobile', '=', vals.get("mobile")), ('x_mobile2', '=', vals.get("mobile")),
                 ('id', '!=', self.id)])
                if partner_id and partner_id.x_brand_id.id == self.x_brand_id.id:
                    raise except_orm('Cảnh báo!', _("Tồn tại khách hàng có số điện thoại này"))
        if 'x_mobile2' in vals and vals['x_mobile2']:
            if vals.get("x_mobile2"):
                partner_id = self.env['res.partner'].search(
                    ['|', '|', ('phone', '=', vals.get("x_mobile2")), ('mobile', '=', vals.get("x_mobile2")), ('x_mobile2', '=', vals.get("x_mobile2")),
                 ('id', '!=', self.id)])
                if partner_id and partner_id.x_brand_id.id == self.x_brand_id.id:
                    raise except_orm('Cảnh báo!', _("Tồn tại khách hàng có số điện thoại này"))
        res = super(ResPartnerCustom, self).write(vals)
        if self.x_images:
            for line in self.x_images:
                if line.name[0:12] == 'update_image':
                    continue
                try:
                    os.mkdir('%s/%s/%s' % (folder_path, folder_filestore, self.x_code))
                except FileExistsError:
                    pass
                except Exception as e:
                    pass
                image_full_path = join('%s/%s/' % (folder_path, folder_filestore), str(self.x_code),
                                       str(line.name + '_' + str(time.time())))
                f = open(image_full_path, 'wb')
                f.write(base64.b64decode(line.datas))
                f.close()
                os.rename(image_full_path, image_full_path + '.png')
                line.name = 'update_image' + line.name
        return res

    def _is_number(self, name):
        try:
            float(name)
            return True
        except ValueError:
            return False

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = self.env['res.partner']
        if self._uid != 1:
            if self._context.get('inventory_product_delivery', False):
                user_obj = self.env['res.users']
                TeamObj = self.env['crm.team']
                # BrandObj = self.env['res.brand']
                EmployeeObj = self.env['hr.employee']
                partner_ids = []
                user = user_obj.search([('id', '=', self._uid)])
                if not user.branch_ids: raise except_orm('Thông báo',
                                                         'Người dùng %s chưa chọn chi nhánh cho phép. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                             str(user.name)))
                for branch in user.branch_ids:
                    if not branch: raise except_orm('Thông báo',
                                                    'Chi nhánh %s chưa chọn thương hiệu. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                        str(branch.name)))
                branch_ids = [user.branch_id and user.branch_id.id or 0]
                for branch in user.branch_ids:
                    branch_ids.append(branch.id)

                team_ids = TeamObj.get_team_ids_by_branches(branch_ids)
                # brand_ids = BrandObj.get_brand_ids_by_branches(branch_ids)
                # - Lấy các partner của các người dùng mà được gắn vào nhân viên là bác sĩ
                employees = EmployeeObj.search([('job_id.x_code', '=', 'BS')])
                for employee in employees:
                    partner_ids.append(employee.user_id.partner_id.id)
                # - Lấy các partner của các người dùng có chọn chi nhánh thuộc chi nhánh cho phép của người đăng nhập
                users_in_branches = user_obj.search([('branch_id', 'in', branch_ids)])
                for u in users_in_branches:
                    partner_ids.append(u.partner_id.id)
                # - Lấy các partner có nhóm bán hàng có chi nhánh thuộc các chi nhánh cho phép của người đăng nhập
                partners = self.search([('x_crm_team_id', 'in', team_ids)])
                for partner in partners:
                    partner_ids.append(partner.id)

                res = self.search(['|', '|', '|', '|', ('name', operator, name), ('x_code', '=', name.upper()),
                                   ('phone', 'ilike', name), ('mobile', 'ilike', name), ('x_mobile2', 'ilike', name), ('id', 'in', partner_ids)],
                                  limit=100)
            elif self._context.get('purchase_order', False):
                res = self.search(['|', '|', '|', '|', ('name', operator, name), ('x_old_code', '=', name.upper()),
                                   ('phone', 'ilike', name), ('mobile', 'ilike', name), ('x_mobile2', 'ilike', name), ('supplier', '=', True)],
                                  limit=100)
            elif self._context.get('stock_picking', False):
                res = self.search(['|', '|', '|', '|', ('name', operator, name), ('x_old_code', '=', name.upper()),
                                   ('phone', 'ilike', name), ('mobile', 'ilike', name), ('x_mobile2', 'ilike', name), ('supplier', '=', True)],
                                  limit=100)
            elif self._context.get('account.cash', False):
                res = self.search(['|', '|', '|', '|', ('name', operator, name), ('x_code', '=', name.upper()),
                                   ('phone', 'ilike', name), ('mobile', 'ilike', name), ('x_mobile2', 'ilike', name)],
                                  limit=100)
            elif self._context.get('reception_customer', False):
                res = self.search(['|', '|', '|', '|', ('phone', '=', name), ('mobile', '=', name), ('x_mobile2', '=', name),
                 ('x_code', '=', name), ('x_old_code', '=', name)], limit=1)
            else:
                user_obj = self.env['res.users']
                TeamObj = self.env['crm.team']
                BrandObj = self.env['res.brand']
                user = user_obj.search([('id', '=', self._uid)])
                if not user.branch_ids: raise except_orm('Thông báo',
                                                         'Người dùng %s chưa chọn chi nhánh cho phép. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                             str(user.name)))
                for branch in user.branch_ids:
                    if not branch: raise except_orm('Thông báo',
                                                    'Chi nhánh %s chưa chọn thương hiệu. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                        str(branch.name)))
                branch_ids = [user.branch_id and user.branch_id.id or 0]
                for branch in user.branch_ids:
                    branch_ids.append(branch.id)

                team_ids = TeamObj.get_team_ids_by_branches(branch_ids)
                brand_ids = BrandObj.get_brand_ids_by_branches(branch_ids)
                if self._is_number(name) == False or (self._is_number(name) == True and len(name) < 10):
                    res = self.search(['|', '|', '|', '|', '|', ('name', operator, name), ('x_code', '=', name.upper()), ('x_old_code', '=', name.upper()),
                                       ('phone', 'ilike', name), ('mobile', 'ilike', name), ('x_mobile2', 'ilike', name),
                                           ('x_crm_team_id', 'in', team_ids)],
                                      limit=100)
                if self._is_number(name) == True and len(name) >= 10:
                    res = self.search(['|','|',
                                       ('phone', 'ilike', name), ('mobile', 'ilike', name), ('x_mobile2', 'ilike', name),
                                       ('x_brand_id', 'in', brand_ids)
                                       ],
                                      limit=100)
                    # if not self._context.get('default_supplier', False):
                    #     user_obj = self.env['res.users']
                    #     TeamObj = self.env['crm.team']
                    #     BrandObj = self.env['res.brand']
                    #     user = user_obj.search([('id', '=', self._uid)])
                    #     if not user.branch_ids: raise except_orm('Thông báo', 'Người dùng %s chưa chọn chi nhánh cho phép. Vui lòng liên hệ quản trị để được giải quyết' % (
                    #                                                    str(user.name)))
                    #     for branch in user.branch_ids:
                    #         if not branch: raise except_orm('Thông báo', 'Chi nhánh %s chưa chọn thương hiệu. Vui lòng liên hệ quản trị để được giải quyết' % (
                    #                                                                 str(branch.name)))
                    #     branch_ids = [user.branch_id and user.branch_id.id or 0]
                    #     for branch in user.branch_ids:
                    #         branch_ids.append(branch.id)
                    #
                    #     team_ids = TeamObj.get_team_ids_by_branches(branch_ids)
                    #     brand_ids = BrandObj.get_brand_ids_by_branches(branch_ids)
                    #     if self._is_number(name) == False or (self._is_number(name) == True and len(name) < 10):
                    #         res = self.search(['|', '|', '|', ('name', operator, name), ('x_code', '=', name.upper()),
                    #                                ('phone', 'ilike', name), ('mobile', 'ilike', name), ('x_crm_team_id', 'in', team_ids)],
                    #                               limit=100)
                    #     if self._is_number(name) == True and len(name) >= 10:
                    #         res = self.search(['|',
                    #                            ('phone', 'ilike', name), ('mobile', 'ilike', name),('x_brand_id','in', brand_ids)
                    #                            ],
                    #                           limit=100)
                    # else:
                    #     res = self.search(['|', '|', '|', ('name', operator, name), ('x_code', '=', name.upper()),
                    #                        ('phone', 'ilike', name), ('mobile', 'ilike', name), ('supplier', '=', True)],
                    #                       limit=100)
        else:
            res = self.search(['|', '|', '|', '|', '|',('name', operator, name), ('x_code', '=', name.upper()), ('x_old_code', '=', name.upper()),
                               ('phone', 'ilike', name), ('mobile', 'ilike', name), ('x_mobile2', 'ilike', name)],
                              limit=100)
        return res.name_get()

    def display_name_team_phone(self):
        result = []
        for record in self:
            phone = record.phone and record.phone or record.mobile or record.x_mobile2 or ''
            team = ''
            if record.x_crm_team_id and record.x_crm_team_id.x_branch_id and record.x_crm_team_id.x_branch_id.code:
                team = record.x_crm_team_id.x_branch_id.code
            name = '%s [%s:%s]' % (str(record.name), str(team), str(phone))
            result.append((record.id, name))
        return result

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            code = record.x_old_code and record.x_old_code or record.x_code or ''
            name = '%s [%s]' % (str(record.name), str(code))
            result.append((record.id, name))
        return result

    @api.depends('name', 'x_code', 'x_old_code')
    def _compute_display_name(self):
        diff = dict(show_address=None, show_address_only=None, show_email=None)
        names = dict(self.with_context(**diff).name_get())
        for partner in self:
            partner.display_name = names.get(partner.id)

    def _generate_customer_code(self, branch_code):
        SequenceObj = self.env['ir.sequence']
        context = {'force_company': 1}
        code_sequence = '%s_partner_code' % (str(branch_code))
        sequence_generate = SequenceObj.with_context(**context).next_by_code(code_sequence)
        if not sequence_generate:
            raise except_orm('Thông báo', 'Không tìm thấy Trình tự mã đối tác có mã: %s' % (code_sequence,))
        return str(sequence_generate)

    def _generate_partner_code(self, partner):
        SequenceObj = self.env['ir.sequence']
        context = {'force_company': 1}
        if partner.is_company:
            sequence_generate = SequenceObj.with_context(**context).next_by_code('company_code')
            code_sequence = 'company_code'
        elif partner.supplier:
            sequence_generate = SequenceObj.with_context(**context).next_by_code('supplier_code')
            code_sequence = 'supplier_code'
        elif partner.customer:
            #mã KH sẽ tạo khi chuyển KH sang trạng thái chốt
            sequence_generate = ''
            return str(sequence_generate)
        else:
            sequence_generate = SequenceObj.with_context(**context).next_by_code('user_code')
            code_sequence = 'user_code'
        if not sequence_generate:
            raise except_orm('Thông báo', 'Không tìm thấy Trình tự sinh mã đối tác có mã: %s' % (code_sequence,))
        return str(sequence_generate)

    def _read_from_database(self, field_names, inherited_field_names=[]):
        super(ResPartnerCustom, self)._read_from_database(field_names, inherited_field_names)
        context = self._context
        if 'phone' in field_names:
            for record in self:
                try:
                    UserObj = http.request.env['res.users']
                    display_phone = UserObj.has_group('izi_display_fields.group_display_phone')
                    if display_phone or self.env.uid == 1:
                        record._cache['phone']
                    else:
                        record._cache['phone']
                        record._cache['phone'] = record._cache['phone'][0:len(record._cache['phone']) - 3] + '***'
                except Exception:
                    pass
        if 'mobile' in field_names:
            for record in self:
                try:
                    UserObj = http.request.env['res.users']
                    display_phone = UserObj.has_group('izi_display_fields.group_display_phone')
                    if display_phone:
                        record._cache['mobile']
                    else:
                        record._cache['mobile']
                        record._cache['mobile'] = record._cache['mobile'][0:len(record._cache['mobile']) - 3] + '***'
                except Exception:
                    pass

    # @api.model
    # def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
    #     context = self._context or {}
    #     res = super(ResPartnerCustom, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
    #                                                         submenu=False)
    #     if not self.env.user.has_group('izi_display_fields.group_display_phone'):
    #         doc = etree.XML(res['arch'])
    #         for node in doc.xpath("//field[@name='phone']"):
    #             # The field you want to modify the attribute
    #             # node = doc.xpath("//field[@name='phone']")[0]
    #             node.set('readonly', '1')
    #             setup_modifiers(node, res['fields']['phone'])
    #             res['arch'] = etree.tostring(doc)
    #         for node in doc.xpath("//field[@name='mobile']"):
    #             # The field you want to modify the attribute
    #             node.set('readonly', '1')
    #             setup_modifiers(node, res['fields']['mobile'])
    #             res['arch'] = etree.tostring(doc)
    #         return res
    #     return res

    # @api.multi
    # def action_copy_image(self):
    #     partner_obj  = self.env['res.partner'].search([('x_code_update', '=', 'SG000001')])
    #     # partner_obj = self.env['res.partner'].search([('id', '=', '81740')])
    #     print( partner_obj)
    #     for x in partner_obj:
    #         if x.x_images:
    #             for line in x.x_images:
    #                 try:
    #
    #                     os.mkdir(folder_path + str(x.x_code))
    #                 except FileExistsError:
    #                     pass
    #                 except Exception as e:
    #                     pass
    #                 image_full_path = join( folder_path, str(x.x_code), str(line.name + '_' + str(time.time())) )
    #                 print(image_full_path)
    #                 f = open( image_full_path , 'wb')
    #                 f.write(base64.b64decode(line.datas))
    #                 f.close()
    #                 os.rename(image_full_path, image_full_path+'.png')
    #                 # line.name = 'update_image' + line.name

    @api.depends('x_birthday')
    def get_level_age(self):
        for partner in self:
            if partner.x_birthday:
                year_birth = int(partner.x_birthday.split('-')[0])
                year_now = datetime.now().year
                age = year_now - year_birth
                partner.x_age = age
                level_age_ids = partner.env['level.age'].search([])
                for level_age_id in level_age_ids:
                    if age in range(level_age_id.age_start, level_age_id.age_end + 1):
                        partner.x_level_age_id = level_age_id.id

    @api.multi
    def action_assign_telesales(self):
        view_id = self.env.ref('res_partner_custom.partner_assign_telesales_form').id
        context = {
            'default_partner_id': self.id,
            'default_telesales_id': self.x_telesales_id.id,
            'default_next_interaction_reminder_activity_type_id': self.x_next_interaction_reminder_activity_type_id.id
        }
        return {
            'name': "Chọn nhân viên telesales",
            'type': 'ir.actions.act_window',
            'res_model': 'partner.assign.telesales',
            'res_id': False,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'context': context,
            'target': 'new',
        }

    @api.multi
    def action_transfer_stage(self):
        view_id = self.env.ref('res_partner_custom.partner_transfer_stage_form').id
        context = {
            'default_partner_id': self.id,
            'default_stage_id': self.x_stage_id.id,
            'default_next_interaction_reminder_activity_type_id': self.x_next_interaction_reminder_activity_type_id.id,
            'default_next_interaction_reminder_date': self.x_next_interaction_reminder_date
        }
        return {
            'name': "Chuyển trạng thái",
            'type': 'ir.actions.act_window',
            'res_model': 'partner.transfer.stage',
            'res_id': False,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'context': context,
            'target': 'new',
        }


class PartnerLevel(models.Model):
    _name = 'level.age'

    name = fields.Char(string='Name Level')
    age_start = fields.Integer(string='Age Start')
    age_end = fields.Integer(string='Age End')
    partner_id = fields.Many2one('res.partner', string='Partner')

    @api.constrains('age_start', 'age_end')
    def _check_value_age(self):
        if not self.age_start and not self.age_end:
            raise ValidationError(_('Dữ liệu độ tuổi nhập vào không hợp lý {} - {}!').format(
                self.age_start, self.age_end))
        if self.age_start >= self.age_end:
            raise ValidationError(_('Lỗi khoảng độ tuổi {} > {}!').format(
                self.age_start, self.age_end))
        for level in self.env['level.age'].search([]):
            if level.age_start < self.age_start < level.age_end or level.age_start < self.age_end < level.age_end:
                raise ValidationError(_('Giá trị độ tuổi {} - {} vào bị trùng với độ tuổi {} - {}!').format(
                    self.age_start, self.age_end, level.age_start, level.age_end))
            result_1 = level.age_start - self.age_start
            result_2 = level.age_end - self.age_end
            if result_1 != 0 and result_2 != 0 and (result_2 * result_1) <= 0:
                raise ValidationError(_('Giá trị độ tuổi {} - {} vào bị trùng với độ tuổi {} - {}!').format(
                    self.age_start, self.age_end, level.age_start, level.age_end))
