# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, http
from odoo.exceptions import except_orm, UserError
from lxml import etree
from odoo.osv.orm import setup_modifiers


class IziCrmLead(models.Model):
    _inherit = 'crm.lead'

    def _default_employee(self):
        empl = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if empl.id != False:
            return empl.id

    def _default_stage_id(self):
        stage = self.env['crm.stage'].search([('x_code', '=', 'lead')], limit=1)
        if not stage:
            self.env['crm.stage'].create({
                'name': _('Lead'),
                'x_code': 'lead',
                'probability': 0
            })
        return stage.id

    def _domain_team_id(self):
        UserObj = self.env['res.users']
        BrandObj = self.env['res.brand']

        user = UserObj.search([('id', '=', self.env.uid)])
        brand_ids = BrandObj.get_brand_ids_by_branches(user.branch_ids.ids)
        return [('x_branch_id.brand_id', 'in', brand_ids), ('team_type', '!=', 'uid_tele')]

    x_employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee)
    x_note = fields.Text('Note')
    # x_stage = fields.Integer(compute='_onchange_stage_id', store=True, copy=False)

    # x_state = fields.Selection([('lead', 'Lead'), ('reference', 'Reference'), ('reference2', 'Reference2'),
    #                             ('opportunity', 'Opportunity'),
    #                             ('to_shop', 'To shop'),
    #                             ('confirm', 'Confirm'),
    #                             ('won', 'Won'),
    #                             ('lose', 'Lose')], default="lead", string="State")
    stage_id = fields.Many2one('crm.stage', string='Stage', track_visibility='onchange', index=True, default=_default_stage_id)

    x_state = fields.Char(related='stage_id.x_code', string='State', store=True, readonly=True)
    x_selection = fields.Selection([
        ('order', 'Order'),
        ('coin', 'Coin'),
        ('deposit', 'Deposit'),
        ('using', 'Using')
    ], default='order', string='Order form')
    name = fields.Char('Opportunity', required=False)
    x_lines = fields.One2many('izi.crm.lead.quotes', 'lead_id', string='Lines')
    x_config_id = fields.Many2one('pos.config', string='Pos Config')
    x_pos_order_ids = fields.One2many('pos.order', 'x_opportunity_id', string='Pos order')
    x_pos_amount_total = fields.Monetary(compute='_compute_pos_amount_total', string="Sum of Orders",
                                       help="Untaxed Total of Confirmed Orders", currency_field='company_currency')
    planned_revenue = fields.Float(compute='_compute_x_quotes',currency_field='company_currency',string='Total', store=True)
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange', default=False)

    x_birthday = fields.Date("BirthDay")
    team_id = fields.Many2one('crm.team', string='Sales Channel', oldname='section_id', domain=_domain_team_id, default=False,
        index=True, track_visibility='onchange', help='When sending mails, the default email address is taken from the sales channel.')
    employee_ids = fields.Many2many('hr.employee', string="Ng?????i h?????ng doanh thu d??? ki???n")
    message_old_lead = fields.Text(string="Th??ng tin lead c??")
    telesale_id = fields.Many2one('res.users', string='Telesale')
    crm_lead_ids = fields.Many2many('crm.lead', 'crm_lead_crm_lead_rel', 'source_lead_id', 'dest_lead_id',
                                     string="History")
    # source_lead_id = fields.Many2one('crm.lead')
    # dest_lead_id = fields.Many2one('crm.lead')

    # @api.multi
    # @api.constrains('x_state', 'stage_id')
    # def _check_x_state_stage_id(self):
    #     for lead in self:
    #         lead.stage_id = self.env['crm.stage'].search([('x_code', '=', lead.x_state)], limit=1).id

    @api.multi
    def edit_dialog(self):
        form_view = self.env.ref('izi_crm_lead.izi_crm_case_form_view_oppor')
        return {
            'name': _('Opportunity'),
            'res_model': 'crm.lead',
            'res_id': self.id,
            'views': [(form_view.id, 'form'), ],
            'type': 'ir.actions.act_window',
            'target': 'inline'
        }

    @api.depends('x_pos_order_ids')
    def _compute_pos_amount_total(self):
        for lead in self:
            total = 0.0
            for order in lead.x_pos_order_ids:
                total += order.amount_total
            lead.x_pos_amount_total = total

    @api.depends('x_lines')
    def _compute_x_quotes(self):
        for lead in self:
            total1 = 0.0
            for order in lead.x_lines:
                total1 = total1 + order.total_amount
            lead.planned_revenue = total1

    @api.multi
    def write(self, vals):
        if 'phone' in vals:
            res = super(IziCrmLead, self).write(vals)
            group_cashier = self.env['res.users'].has_group('izi_res_permissions.group_cashier')
            if self.x_state == 'confirm':
                if not self.user_id:
                    raise except_orm('C???nh b??o!', _("Ch??a c?? nh??n vi??n b??n h??ng (t?? v???n)!"))
                if self.env.uid != 1 and not group_cashier and self.user_id.id != self.env.uid:
                    raise except_orm('C???nh b??o!', _("????n n??y kh??ng ph???i giao cho b???n, b???n kh??ng ???????c x??c nh???n!"))
            lead_ids = self.env['crm.lead'].search([('phone', '=', self.phone), ('id', '!=', self.id)])
            if not lead_ids:
                self.crm_lead_ids = None
            else:
                self.crm_lead_ids = [(6, 0, lead_ids.ids)]
        return super(IziCrmLead, self).write(vals)

    @api.model
    def create(self, vals):
        lead_ids = self.env['crm.lead'].search([('phone', '=', vals.get('phone'))])
        vals['crm_lead_ids'] = [(6, 0, lead_ids.ids)]
        res = super(IziCrmLead, self).create(vals)
        return res

    @api.onchange('partner_name')
    def _onchange_name_lead(self):
        if not self.name:
            self.name = self.partner_name
            
    @api.onchange('team_id')
    def _onchange_team_id(self):
        list = []
        UserObj = self.env['res.users']
        user = UserObj.search([('id', '=', self._uid)])
        if self.team_id:
            job = self.env['hr.job'].search([('x_code', '=', 'NVTV')], limit=1)
            if job.id == False:
                raise except_orm('C???nh b??o!', _("Ch??a c???u h??nh ch???c v??? cho nh??n vi??n t?? v???n: NVTV"))
            for user in self.team_id.x_member_ids:
                # employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
                employee = self.env['hr.employee'].search(
                    ['|', ('user_id', '=', user.id), ('x_user_ids', 'in', user.id)], limit=1)
                if employee.id == False:
                    continue
                # S??ng la comment l???i ng??y 18/6/2019 do c?? th??? giao 1 l??c nhi???u lead.
                if employee.job_id.id == job.id:
                    # stage_id = self.env['crm.stage'].search([('name', '=', 'X??c nh???n')], limit=1)
                    # lead_ids = self.env['crm.lead'].search([('stage_id', '=', stage_id.id), ('user_id', '=', user.id)])
                    # if len(lead_ids) == 0:
                    list.append(user.id)
            x_config_id = self.env['pos.config'].search([('crm_team_id', '=', self.team_id.id)], limit=1)
            self.x_config_id = x_config_id.id
            if self.phone:
                self._onchange_partner()

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id:
            employee = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)])
            if not employee: raise UserError('Ch??a t???o nh??n vi??n cho ng?????i d??ng %s.' % (str(self.user_id.name)))
            if len(employee) > 1: raise UserError('C?? nhi???u h??n m???t nh??n vi??n ??ang li??n k???t ?????n t??i kho???n ng?????i d??ng %s. %s' % (str(self.user_id.name), str(employee.ids)))
            employee_ids = []
            employee_ids.append(employee.id)
            if self.employee_ids:
                for employee_id in self.employee_ids:
                    employee_ids.append(employee_id.id)
            return {
                'value': {
                    'employee_ids': [[6, 0, employee_ids]]
                }
            }

    @api.onchange('phone')
    def _onchange_partner(self):
        if self.phone:
            # l???y kh??ch h??ng
            user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
            if not user: raise UserError('Kh??ng t??m th???y ng?????i d??ng c?? id: %s' % (str(self._uid)))
            if not user.branch_id: raise UserError('Ng?????i d??ng %s ch??a ???????c c???u h??nh chi nh??nh' % (str(user.name)))
            brand = user.branch_id.brand_id
            partner_id = self.env['res.partner'].search(
                ['|', ('phone', '=', self.phone), ('mobile', '=', self.phone), ('x_brand_id', '=', brand.id)], limit=1)
            if partner_id:
                self.partner_id = partner_id.id
                self.source_id = partner_id.source_id.id if partner_id.source_id else False
            # L???y lead c?? ??? trang th??i m???i v?? x??c nh???n
            leads = self.search([('phone', '=', self.phone)])
            message_old_lead = ''
            if leads:
                message_old_lead += 'C??c c?? h???i ???? t???o cho s??? ??i???n tho???i %s: \n' % (str(self.phone))
                for lead in leads:
                    str_employees = ''
                    if lead.employee_ids:
                        for employee in lead.employee_ids:
                            str_employees += '%s, ' % (str(employee.name))
                    message_old_lead += 'C?? h???i: %s | Nh??m b??n h??ng: %s | Nh??n vi??n b??n h??ng: %s | Nh??n vi??n h?????ng doanh thu d??? ki???n: %s | Ghi ch??: %s | Tr???ng th??i: %s \n' \
                                        % (str(lead.name), str(lead.team_id.name), str(lead.user_id and lead.user_id.name or ''), str(str_employees), str(lead.description and lead.description or ''), str(lead.stage_id.name))
            self.message_old_lead = message_old_lead

    @api.onchange('partner_id')
    def _onchange_name(self):
        if not self.partner_id:
            self.partner_name = False
            self.phone = False
            self.mobile = False
            self.x_birthday = False

    def _onchange_partner_id_values(self, partner_id):
        """ returns the new values when partner_id has changed """
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            return {
                'partner_name': partner.name,
                'contact_name': partner.name,
                'title': partner.title.id,
                'street': partner.street,
                'street2': partner.street2,
                'city': partner.city,
                'state_id': partner.state_id.id,
                'country_id': partner.country_id.id,
                'email_from': partner.email,
                'phone': partner.phone,
                'mobile': partner.mobile,
                'zip': partner.zip,
                'function': partner.function,
                'website': partner.website,
            }
        return {}

    @api.multi
    def action_set_lost(self):
        for lose in self:
            stage_id = self.env['crm.stage'].search([('x_code', '=', 'lose')])
            if not stage_id:
                stage_id = self.env['crm.stage'].create({
                    'name': _('Lose'),
                    'x_code': 'lose',
                    'probability': 0
                })
            lose.stage_id = stage_id.id

    @api.multi
    def action_confirm(self):
        group_cashier = self.env['res.users'].has_group('izi_res_permissions.group_cashier')
        if not self.user_id:
            raise except_orm('C???nh b??o!', _("Ch??a c?? nh??n vi??n b??n h??ng (t?? v???n)!"))
        if self.env.uid != 1 and not group_cashier and self.user_id.id != self.env.uid:
            raise except_orm('C???nh b??o!', _("????n n??y kh??ng ph???i giao cho b???n, b???n kh??ng ???????c x??c nh???n!"))
        stage_id = self.env['crm.stage'].search([('x_code', '=', 'confirm')], limit=1)
        self.stage_id = stage_id.id

    @api.multi
    def action_quotes(self):
        if len(self.x_lines) == 0:
            raise except_orm('C???nh b??o!', _("B???n ch??a th??m s???n ph???m cho ????n b??o gi?? d??? ki???n"))
        # self.x_stage = 3
        stage_id = self.env['crm.stage'].search([('x_code', '=', 'shop')], limit=1)
        self.stage_id = stage_id.id
        pass

    @api.multi
    def action_order(self):
        self.action_create_customer()
        view = self.env.ref('izi_crm_lead.izi_create_form_view_oppor')
        return {
            'name': _('Choice create form'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'crm.lead',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': self.env.context,
        }

    @api.multi
    def action_pos(self):
        current_session = self.env['pos.session'].search(
            [('state', '=', 'opened'), ('config_id', '=', self.x_config_id.id)], limit=1)
        if not current_session:
            raise except_orm(("C???nh b??o!"), _('B???n ph???i m??? phi??n tr?????c khi t???o ????n h??ng m???i.'))
        stage_id = self.env['crm.stage'].search([('x_code', '=', 'won')], limit=1)
        self.stage_id = stage_id.id
        if len(self.x_lines) != 0:
            if self.x_selection == 'order':
                employee_ids = []
                for employee in self.employee_ids:
                    employee_ids.append(employee.id)
                PosOrder = self.env['pos.order']
                argv = {
                    'session_id': current_session.id,
                    'partner_id': self.partner_id.id,
                    'state': 'draft',
                    'x_opportunity_id': self.id,
                    'user_id': self.user_id.id,
                    'x_user_id': [(4, x) for x in employee_ids]
                }
                order_id = PosOrder.create(argv)
                for line in self.x_lines:
                    line = {
                        'product_id': line.product_id.id,
                        'qty': line.qty,
                        'price_unit': line.price_unit,
                        'order_id': order_id.id,
                    }
                    PosOrder = self.env['pos.order.line'].create(line)
                view = self.env.ref('point_of_sale.view_pos_pos_form')
                context = self.env.context.copy()
                context.update({'lead_employee_ids': self.employee_ids.ids})
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.order',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'res_id': order_id.id,
                    'target': '',
                    'context': context,
                }
            elif self.x_selection == 'using':
                employee_ids = []
                for employee in self.employee_ids:
                    employee_ids.append(employee.id)
                Using = self.env['izi.service.card.using']
                context = self.env.context.copy()
                argv = {
                    'session_id': current_session.id,
                    'customer_id': self.partner_id.id,
                    'state': 'draft',
                    'x_opportunity_id': self.id,
                    'user_id': self.user_id.id,
                    'type': 'service',
                    'x_user_id': [(4, x) for x in employee_ids],
                }
                using_id = Using.create(argv)
                for line in self.x_lines:
                    if line.product_id.product_tmpl_id.type == 'service' and line.product_id.default_code != 'COIN':
                        line = {
                            'service_id': line.product_id.id,
                            'quantity': line.qty,
                            'price_unit': line.price_unit,
                            'using_id': using_id.id,
                        }
                        Detail = self.env['izi.service.card.using.line'].create(line)
                view = self.env.ref('izi_use_service_card.use_service_card_form')
                context.update({'lead_employee_ids': self.employee_ids.ids})
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'izi.service.card.using',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'res_id': using_id.id,
                    'target': '',
                    'context': context,
                }
            elif self.x_selection == 'merge_service':
                user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
                config_id = user_id.x_pos_config_id.id

                current_session = self.env['pos.session'].search(
                    [('state', '=', 'opened'), ('config_id', '=', config_id)], limit=1)
                if not current_session:
                    raise except_orm(("C???nh b??o!"), _('B???n ph???i m??? phi??n tr?????c khi t???o ????n h??ng m???i.'))
                partner_obj = self.env['res.partner'].search([('id', '=', self.partner_id.id)])
                if len(partner_obj) > 1:
                    raise except_orm('Th??ng b??o!', ("C?? 2 KH c?? trung m??. VUi l??ng li??n h??? Admintrantor"))
                if len(partner_obj) == 0:
                    raise except_orm('Th??ng b??o!', ("Kh??ng c?? m?? KH. VUi l??ng li??n h??? Admintrantor"))
                ctx = self.env.context.copy()
                ctx.update({'default_partner_search_id': partner_obj.id,
                            'default_session_id': current_session.id,
                            })
                view = self.env.ref('izi_merge_use_service.merge_use_service_form')
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'merge.use.service',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    # 'res_id': using_id.id,
                    'target': '',
                    'context': ctx,
                }
            elif self.x_selection == 'deposit':
                ctx = self.env.context.copy()
                ctx.update(
                    {'default_partner_id': self.partner_id.id, 'default_x_type': 'deposit', 'default_type': 'deposit',
                     'default_x_opportunity_id': self.id, 'default_session_id': current_session.id,
                     'default_user_id': self.user_id.id,
                     'lead_employee_ids': self.employee_ids.ids})
                # deposit = self.env['pos.customer.deposit.line']
                # argv = {
                #     'session_id': current_session.id,
                #     'partner_id': self.partner_id.id,
                #     'state': 'draft',
                #     'x_opportunity_id': self.id,
                #     'user_id': self.user_id.id
                # }
                # deposit_id = deposit.create(argv)
                view = self.env.ref('pos_customer_deposit.pos_customer_deposit_line_form_view')
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.customer.deposit.line',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': '',
                    'context': ctx,
                }
            else:
                PosOrder = self.env['pos.order']
                employee_ids = []
                for employee in self.employee_ids:
                    employee_ids.append(employee.id)
                context = self.env.context.copy()
                argv = {
                    'session_id': current_session.id,
                    'partner_id': self.partner_id.id,
                    'state': 'draft',
                    'x_opportunity_id': self.id,
                    'user_id': self.user_id.id,
                    'x_user_id': [(4, x) for x in employee_ids],
                    'x_type': '2'
                }
                order_id = PosOrder.create(argv)
                product_id = self.env['product.product'].search([('default_code', '=', 'COIN')], limit=1)
                line = {
                    'product_id': product_id.id,
                    'qty': 1,
                    'price_unit': 1,
                    'order_id': order_id.id,
                }
                PosOrder = self.env['pos.order.line'].create(line)
                view = self.env.ref('izi_virtual_money.view_pos_pos_form_izi_vm_sell')
                context.update({'lead_employee_ids': self.employee_ids.ids})
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.order',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'res_id': order_id.id,
                    'target': '',
                    'context': self.env.context,
                }

        else:
            if self.x_selection == 'order':
                ctx = self.env.context.copy()
                ctx.update(
                    {'default_partner_id': self.partner_id.id, 'default_x_opportunity_id': self.id,
                     'default_user_id': self.user_id.id, 'default_session_id': current_session.id,
                     'lead_employee_ids': self.employee_ids.ids, 'default_x_type': '1'})
                view = self.env.ref('point_of_sale.view_pos_pos_form')
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.order',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': '',
                    'context': ctx,
                }

            elif self.x_selection == 'using':
                ctx = self.env.context.copy()
                ctx.update({'default_customer_id': self.partner_id.id, 'default_type': 'service',
                            'default_x_opportunity_id': self.id, 'default_session_id': current_session.id,
                            'default_user_id': self.user_id.id,
                            'lead_employee_ids': self.employee_ids.ids})
                view = self.env.ref('izi_use_service_card.use_service_card_form')
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'izi.service.card.using',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': '',
                    'context': ctx,
                }
            elif self.x_selection == 'merge_service':
                user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
                config_id = user_id.x_pos_config_id.id

                current_session = self.env['pos.session'].search(
                    [('state', '=', 'opened'), ('config_id', '=', config_id)], limit=1)
                if not current_session:
                    raise except_orm(("C???nh b??o!"), _('B???n ph???i m??? phi??n tr?????c khi t???o ????n h??ng m???i.'))
                partner_obj = self.env['res.partner'].search([('id', '=', self.partner_id.id)])
                if len(partner_obj) > 1:
                    raise except_orm('Th??ng b??o!', ("C?? 2 KH c?? trung m??. VUi l??ng li??n h??? Admintrantor"))
                if len(partner_obj) == 0:
                    raise except_orm('Th??ng b??o!', ("Kh??ng c?? m?? KH. VUi l??ng li??n h??? Admintrantor"))
                ctx = self.env.context.copy()
                ctx.update({'default_partner_search_id': partner_obj.id,
                            'default_session_id': current_session.id,
                            })
                view = self.env.ref('izi_merge_use_service.merge_use_service_form')
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'merge.use.service',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    # 'res_id': using_id.id,
                    'target': '',
                    'context': ctx,
                }
            elif self.x_selection == 'deposit':
                ctx = self.env.context.copy()
                ctx.update(
                    {'default_partner_id': self.partner_id.id, 'default_x_type': 'deposit', 'default_type': 'deposit',
                     'default_x_opportunity_id': self.id, 'default_session_id': current_session.id,
                     'default_user_id': self.user_id.id,
                     'lead_employee_ids': self.employee_ids.ids})
                # deposit = self.env['pos.customer.deposit.line']
                # argv = {
                #     'session_id': current_session.id,
                #     'partner_id': self.partner_id.id,
                #     'state': 'draft',
                #     'x_opportunity_id': self.id,
                #     'user_id': self.user_id.id
                # }
                # deposit_id = deposit.create(argv)
                view = self.env.ref('pos_customer_deposit.pos_customer_deposit_line_form_view')
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.customer.deposit.line',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': '',
                    'context': ctx,
                }
            else:
                ctx = self.env.context.copy()
                ctx.update(
                    {'default_partner_id': self.partner_id.id, 'izi_sell_vm': True, 'default_x_opportunity_id': self.id,
                     'default_user_id': self.user_id.id, 'default_session_id': current_session.id,
                     'lead_employee_ids': self.employee_ids.ids, 'default_x_type': '2'})
                view = self.env.ref('izi_virtual_money.view_pos_pos_form_izi_vm_sell')
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.order',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': '',
                    'context': ctx,
                }

    @api.multi
    def action_search(self):
        search_card_obj = self.env['izi.product.search.card'].create({
            'brand_id': self.partner_id.x_brand_id.id,
            'serial': self.partner_id.phone,
        })
        search_card_obj.action_check_card()
        ctx = self.env.context.copy()
        # ctx.update(
        #     {'default_serial': self.partner_id.phone})
        view = self.env.ref('izi_product_search_card.izi_product_search_card_form')
        return {
            'name': _('Search partner'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'izi.product.search.card',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': '',
            'context': ctx,
            'res_id': search_card_obj.id,
        }

    @api.multi
    def action_create_customer(self):
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
                'source_id': self.source_id.id,
            }
            partner_id = self.env['res.partner'].create(vals)
            self.partner_id = partner_id.id

    # def _read_from_database(self, field_names, inherited_field_names=[]):
    #     super(IziCrmLead, self)._read_from_database(field_names, inherited_field_names)
    #     if 'phone' in field_names:
    #         for record in self:
    #             try:
    #                 UserObj = http.request.env['res.users']
    #                 display_phone = UserObj.has_group('izi_display_fields.group_display_phone')
    #                 if display_phone:
    #                     record._cache['phone']
    #                 else:
    #                     record._cache['phone']
    #                     record._cache['phone'] = record._cache['phone'][0:6]+'***'
    #             except Exception:
    #                 pass
    #             except Exception:
    #                 pass

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        context = self._context or {}
        res = super(IziCrmLead, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                            submenu=False)
        if not self.env.user.has_group('izi_display_fields.group_display_phone'):
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='phone']"):
                # The field you want to modify the attribute
                # node = doc.xpath("//field[@name='phone']")[0]
                node.set('readonly', '1')
                setup_modifiers(node, res['fields']['phone'])
                res['arch'] = etree.tostring(doc)
            return res
        return res