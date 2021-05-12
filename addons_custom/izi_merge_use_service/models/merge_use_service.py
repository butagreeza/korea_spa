# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm

class MergeUseService(models.Model):
    _name = 'merge.use.service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    def _default_pos_session(self):
        pos_session = self.env['pos.session']
        pos_config_id = self.env.user.x_pos_config_id.id
        my_session = pos_session.search([('config_id', '=', pos_config_id), ('state', '=', 'opened')])
        if not my_session:
            return False
        else:
            return my_session.id

    name = fields.Char("Name", default='/')
    serial_code = fields.Char("Serial Code", track_visibility='onchange')
    redeem_date = fields.Datetime("Redeem Date", default=fields.Datetime.now, track_visibility='onchange')
    customer_id = fields.Many2one('res.partner', "Customer", track_visibility='onchange')
    pricelist_id = fields.Many2one('product.pricelist', "Pricelist", track_visibility='onchange')
    state = fields.Selection([('draft', "Draft"), ('wait_payment', "Wait Payment"), ('wait_approve', "Wait Approve"),
                              ('wait_material', "Wait Material"),
                              ('working', "Working"), ('rate', "Rate"), ('done', "Done"),
                              ('wait_confirm', "Wait Confirm"), ('wait_delivery', "Wait Delivery"),
                              ('cancel', "Cancel")], default='draft', track_visibility='onchange')

    # old_image_ids = fields.One2many('izi.images', 'old_service_card_id', string='Image')
    # new_image_ids = fields.One2many('izi.images', 'new_service_card_id', string='Image')
    pos_order_id = fields.Many2one('pos.order', "Pos Order", track_visibility='onchange')
    pos_order_refund_id = fields.Many2one('pos.order', "Pos Order Refund", track_visibility='onchange')
    date_start = fields.Datetime("Date Start", track_visibility='onchange')
    date_end = fields.Datetime("Date End", track_visibility='onchange')
    signature_image = fields.Binary("Signature Image", default=False, attachment=True, track_visibility='onchange')
    amount_total = fields.Float("Amount Total", compute='_compute_amount_total')
    user_id = fields.Many2one('res.users', "User", default=lambda self: self.env.uid)
    pos_session_id = fields.Many2one('pos.session', "Pos Session", default=_default_pos_session)
    debt_amount = fields.Float('Debt Amount', compute='_compute_amount')
    payment_amount = fields.Float("Payment Amount", compute='_compute_amount')
    option_refund = fields.Selection([('cancel', "Cancel"), ('refund', "Refund")])
    note = fields.Text("Note")
    # Sangla thêm ngày 23/10/2018 them chọn khách hàng ra số điện thoại để seach
    partner_search_id = fields.Many2one('res.partner', "Partner Search")
    use_service_ids = fields.One2many('merge.use.service.service', 'merge_service_id', "Use Service")
    use_service_card_ids = fields.One2many('merge.use.service.card', 'merge_service_id', "Use Service Card")
    use_service_guarantee_ids = fields.One2many('merge.use.service.guarantee', 'merge_service_id', "Use Service Card")
    pos_payment_service_ids = fields.One2many('merge.pos.payment.service', 'merge_using_service_id', "Merge Pos Payment Service")
    use_material_ids = fields.One2many('pos.user.material', 'merge_service_id', "Use Material")

    def _get_material_user(self,quantity,product_id, use_service_id, line_service):
        if product_id.bom_service_count <= 0 and product_id.product_tmpl_id.x_type_service  == 'spa' and self.type != 'guarantee':
            raise except_orm('Cảnh báo!', "Chưa cấu hình nguyên vật liệu sử dụng cho dịch vụ này")
        else:
            # action = self.env.ref('izi_use_service_card.tmp_pos_use_material_view')quantity
            line = []
            bom_id = False
            tmp_service = self.env['merge.tmp.service.card.using']
            tmp_service_line = self.env['merge.tmp.service.card.using.line']
            tmp_service_obj = self.env['merge.tmp.service.card.using'].search([('user_service_card_id', '=', use_service_id)])
            if tmp_service_obj:
                for tmp in product_id.bom_service_ids:
                    if not tmp.product_id or tmp.product_id == product_id:
                        bom_id = tmp.id
                        break
                i = quantity
                while (i > 0):
                    i -= 1
                    if product_id.bom_service_count >1:
                        vals = {
                            'product_id': product_id.id,
                            'bom_id': bom_id if bom_id else False,
                            'qty_using': 1,
                            'tmp_service_card_using': tmp_service_obj.id,
                            'user_service_card_line_id': line_service.id,
                        }
                        tmp_service_line.create(vals)
                    else:
                        vals = {
                            'product_id': product_id.id,
                            'bom_id': bom_id if bom_id else False,
                            'qty_using': quantity,
                            'tmp_service_card_using': tmp_service_obj.id,
                            'user_service_card_line_id': line_service.id,
                        }
                        tmp_service_line.create(vals)
                        break
            else:
                tmp_service_id = self.env['merge.tmp.service.card.using'].create({'user_service_card_id': use_service_id})
                for tmp in product_id.bom_service_ids:
                    if not tmp.product_id or tmp.product_id == product_id:
                        bom_id = tmp.id
                        break
                i = quantity
                while (i > 0):
                    i -= 1
                    if product_id.bom_service_count >1:
                        vals = {
                            'product_id': product_id.id,
                            'bom_id': bom_id if bom_id else False,
                            'qty_using': 1,
                            'tmp_service_card_using': tmp_service_id.id,
                            'user_service_card_line_id': line_service.id,
                        }
                        tmp_service_line.create(vals)
                    else:
                        vals = {
                            'product_id': product_id.id,
                            'bom_id': bom_id if bom_id else False,
                            'qty_using': quantity,
                            'tmp_service_card_using': tmp_service_id.id,
                            'user_service_card_line_id': line_service.id,
                        }
                        tmp_service_line.create(vals)
                        break

    @api.model
    def default_get(self, fields):
        res = super(MergeUseService, self).default_get(fields)
        if not self._context.get('inventory_update', False):
            current_session = self.env['pos.session'].search(
                [('state', '!=', 'closed'), ('config_id', '=', self.env.user.x_pos_config_id.id)], limit=1)
            if not current_session:
                raise except_orm(("Cảnh báo!"), ('Bạn phải mở phiên trước khi tạo đơn hàng mới.'))
        return res

    @api.depends('use_service_ids.quantity', 'use_service_ids.price_unit', 'use_service_guarantee_ids.quantity','use_service_guarantee_ids.quantity')
    def _compute_amount_total(self):
        for line in self:
            for tmp in line.use_service_ids:
                line.amount_total += tmp.amount
            for tmp in line.use_service_guarantee_ids:
                line.amount_total += tmp.amount

    @api.depends('pos_payment_service_ids')
    def _compute_amount(self):
        money = 0
        journal_debt_id = self.pos_session_id.config_id.journal_debt_id.id if self.pos_session_id.config_id.journal_debt_id else False
        if journal_debt_id:
            for statement in self.pos_payment_service_ids:
                if statement.journal_id.id == journal_debt_id:
                    money += statement.amount
        self.debt_amount = money
        self.payment_amount = self.amount_total - money

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('merge.use.service') or _('New')
        return super(MergeUseService, self).create(vals)

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Cảnh báo!', ('Bạn không thể xóa khi khác trạng thái nháp'))
        return super(MergeUseService, self).unlink()

    @api.onchange('customer_id')
    def onchange_customer_id(self):
        if self.customer_id:
            self.pricelist_id = self.customer_id.property_product_pricelist.id

    @api.multi
    def action_send_price(self):
        count = 0
        if self.state != 'draft':
            raise except_orm("Cảnh báo!", ("Trạng thái đơn sử dụng đã thay đổi. Vui lòng F5 hoặc tải lại trang"))
        for line in self.use_service_card_ids:
            if line.quantity == 0:
                line.unlink()
            else:
                if (len(line.employee_ids) + len(line.doctor_ids)) == 0:
                    raise except_orm('Cảnh báo!', ('Bạn cần chọn kỹ thuật viên trước khi xác nhận'))
        for line in self.use_service_ids:
            count += 1
            if (len(line.employee_ids) + len(line.doctor_ids)) == 0:
                raise except_orm('Cảnh báo!', ('Bạn cần chọn kỹ thuật viên trước khi xác nhận'))
        for line in self.use_service_guarantee_ids:
            count += 1
            if (len(line.employee_ids) + len(line.doctor_ids)) == 0:
                raise except_orm('Cảnh báo!', ('Bạn cần chọn kỹ thuật viên trước khi xác nhận'))
        if self.env.context.get('default_type', False):
            context = dict(self.env.context or {})
            del context['default_type']
            self = self.with_context(context)
        if not self.customer_id:
            raise except_orm('Cảnh báo!', ("Bạn phải chọn khách hàng trước khi xác nhận!"))
        pos_session = self.env['pos.session']
        pos_config_id = self.env.user.x_pos_config_id.id
        my_session = pos_session.search([('config_id', '=', pos_config_id), ('state', '=', 'opened')])
        if not my_session:
            raise except_orm("LỖI", "Không có phiên POS nào đang mở. Xin hãy mở phiên trước khi thao tác !!")
        for line in self.use_service_card_ids:
            if line.serial_id.x_release_id.use_type == '0':
                if line.serial_id.x_customer_id.id != self.customer_id.id:
                    raise except_orm('Cảnh báo!', ("Thẻ này là đích danh không thể sử dụng cho khách hàng khác!"))
            if line.quantity != 0:
                count += 1
        if count == 0:
            raise except_orm('Cảnh báo!',
                             ("Số lượng dịch vụ không thể bằng không.Vui lòng xóa hoặc thay đổi số lượng!"))
        msg = []
        approve_price = False
        for line in self.use_service_ids:
            price = self.pricelist_id.get_product_price(line.service_id, line.quantity or 1.0, self.customer_id)
            if line.price_unit < price:
                approve_price = True
                msg.append('Dịch vụ %s ' % (line.service_id.name))
                msg.append('Giá niêm yết %r ' % self.convert_numbers_to_text_sangla(price))
                msg.append('Giá bán %r ' % self.convert_numbers_to_text_sangla(line.price_unit))
                msg.append('Dưới mức giá bán tối thiểu cần phê duyêt. ')
        for line in self.use_service_guarantee_ids:
            if line.service_id.x_guarantee != True:
                approve_price = True
                msg.append('Dịch vụ %s ' % (line.service_id.name))
                msg.append('bảo hành cần phê duyệt')
        if approve_price == True:
            self.state = 'wait_approve'
            values = {'state': 'wait_approve'}
            # Thông báo quản lý phê duyệt
            values['message_follower_ids'] = []
            users = self.env['res.users'].search([
                ('groups_id', 'in', self.env.ref('point_of_sale.group_pos_manager').id),
                ('id', '!=', self._uid)])
            MailFollowers = self.env['mail.followers']
            follower_partner_ids = []
            for m in self.message_follower_ids:
                follower_partner_ids.append(m.partner_id.id)
            for user in self.user_id:
                if user.x_pos_config_id.id == self.pos_session_id.config_id.id and \
                        user.partner_id.id and user.partner_id.id not in follower_partner_ids:
                    values['message_follower_ids'] += \
                        MailFollowers._add_follower_command(self._name, [], {user.partner_id.id: None}, {})[0]
            self.write(values)
            self.message_post(subtype='mt_activities',
                              body=" %s !" % (' ' + ', '.join(msg) if len(msg) else ''))
            return {'type': 'ir.actions.act_window_close'}
        else:
            self.state = 'wait_payment'

    @api.multi
    def action_manager_confirm(self):
        if self.state != 'wait_approve':
            raise except_orm("Cảnh báo!", ("Trạng thái đơn sử dụng đã thay đổi. Vui lòng F5 hoặc tải lại trang"))
        self.state = 'wait_payment'


    @api.multi
    def payment_service(self):
        # self.action_compute_order_discount()
        if self.env.context is None:
            context = {}
        ctx = self.env.context.copy()
        ctx.update({'default_merge_using_service_id': self.id})
        view = self.env.ref('izi_merge_use_service.view_pop_up_merge_pos_payment_service')
        return {
            'name': _('Payment Service'),
            'type': 'ir.actions.act_window',
            'res_model': 'merge.pos.payment.service',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_back(self):
        self.state = 'draft'
        for line in self.pos_payment_service_ids:
            line.unlink()

    @api.multi
    def action_confirm(self):
        if self.debt_amount + self.payment_amount < self.amount_total:
            raise except_orm('Cảnh báo!', ("Bạn phải thanh toán trước khi xác nhận đơn sử dụng dịch vụ"))
        if len(self.use_service_card_ids) > 0:
            self.action_create_use_service('card', self.use_service_card_ids)
        if len(self.use_service_ids) > 0:
            self.action_create_use_service('service', self.use_service_ids, self.pos_payment_service_ids)
        if len(self.use_service_guarantee_ids) > 0:
            self.action_create_use_service('guarantee', self.use_service_guarantee_ids)
        



    # Tạo các đơn sử dụng dịch vụ lẻ ứng với từng trường hợp
    @api.multi
    def action_create_use_service(self, type, lines, payment_ids):
        use_service_card = self.env['izi.service.card.using']
        use_service_card_line = self.env['izi.service.card.using.line']
        pos_payment = self.env['pos.payment.service']
        use_service_card_id = use_service_card.create({
            'type': type,
            'customer_id': self.customer_id.id,
            'pricelist_id': self.pricelist_id.id,
            'redeem_date': self.redeem_date,
            'merge_service_id': self.id,
            'user_id': self.user_id.id,
            'pos_session_id': self.pos_session_id.id,
        })
        for line in lines:
            use_service_card_line_id = use_service_card_line.create({
                'service_id': line.service_id.id,
                'max_use_count': line.max_use_count,
                'paid_count': line.paid_count,
                'used_count': line.used_count,
                'quantity': line.quantity,
                'uom_id': line.uom_id.id,
                'employee_ids': line.employee_ids.ids,
                'serial_id': line.serial_id.id,
                'detail_serial_id': line.detail_serial_id,
                'price_unit': line.price_unit,
                'discount': line.discount,
                'amount': line.amount,
                'is_gift': line.is_gift,
                'doctor_ids': line.doctor_ids.ids,
                'branch_id': line.branch_id.id,
                'show_button': line.show_button,
                'guarantee_id': line.guarantee_id,
                'using_id': use_service_card_id.id,
            })
        for x in payment_ids:
            pos_payment_id = pos_payment.create({
                'x_show_vm_amount': x.x_show_vm_amount,
                'x_vm_amount_total': x.x_vm_amount_total,
                'x_partner_id': x.x_partner_id.id,
                'x_lock_amount': x.x_lock_amount,
                'x_show_vc_code': x.x_show_vc_code,
                'x_vc_code': x.x_vc_code,
                'journal_id': x.journal_id.id,
                'amount': x.amount,
                'x_deposit_amount_residual': x.x_deposit_amount_residual,
                'x_show_deposit_amount': x.x_show_deposit_amount,
                'using_service_id': use_service_card_id.id,
            })
        return use_service_card_id