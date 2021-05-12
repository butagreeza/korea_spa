# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError, MissingError, except_orm
import logging


class TherapyPrescription(models.Model):
    _name = 'therapy.prescription'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin']

    name = fields.Char(string='Therapy prescription', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Partner', track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='Prescriber', track_visibility='onchange')
    create_date = fields.Datetime(string='Create Date', default=fields.Datetime.now)
    time_prescription = fields.Datetime(string='Prescription Time', default=fields.Datetime.now, track_visibility='onchange')
    note = fields.Text(string='Note')
    state = fields.Selection([('draft', 'Draft'), ('waiting', 'Waiting'),
                              ('transfer_confirmation', 'Transfer confirmation'),
                              ('confirm', 'Confirm'), ('cancel', 'Cancel')], default='draft',
                             string='State', track_visibility='onchange')
    therapy_prescription_line_warranty_ids = fields.One2many('therapy.prescription.line', 'therapy_prescription_id',
                                                             string='Therapy prescription line',
                                                             domain=lambda self: [('type', '=', 'warranty')])
    therapy_prescription_line_remain_ids = fields.One2many('therapy.prescription.line', 'therapy_prescription_id',
                                                           string='Therapy prescription line',
                                                           domain=lambda self: [('type', '=', 'remain')])
    therapy_prescription_line_medicine_ids = fields.One2many('therapy.prescription.line', 'therapy_prescription_id',
                                                             string='Therapy prescription line',
                                                             domain=lambda self: [('type', '=', 'medicine')])
    therapy_record_id = fields.Many2one('therapy.record', 'Therapy Record')
    izi_service_card_using_ids = fields.One2many('izi.service.card.using', 'therapy_prescription_id',
                                                 string='Using service card')
    stock_picking_ids = fields.One2many('stock.picking', 'x_therapy_prescription_id', string='Stock Picking')
    get_medicine = fields.Boolean(string='Get Medicine', default=False)
    therapy_prescription_return_product_line_ids = fields.One2many('therapy.prescription.return.product.line', 'therapy_prescription_id', string='Therapy Prescription Return Product')
    is_create_stock_picking = fields.Boolean(string='Is create picking', default=False)
    check_invisible_button_approve = fields.Boolean(default=False, compute='_check_invisible_button_approve')
    config_id = fields.Many2one('pos.config', related='user_id.x_pos_config_id', string='Pos Config', readonly=True)
    location_id = fields.Many2one('stock.location', related='config_id.stock_location_id', string='Stock Location', readonly=True)
    state_using = fields.Selection([('open', 'Open'), ('close', 'Close')], string='State Using')
    state_picking = fields.Selection([('open', 'Open'), ('close', 'Close')], string='State Picking')

    @api.depends('therapy_prescription_return_product_line_ids')
    def _check_invisible_button_approve(self):
        for line in self:
            if line.therapy_prescription_return_product_line_ids:
                self.check_invisible_button_approve = True
            else:
                self.check_invisible_button_approve = False

    # todo kiểm tra xem có chọn ngày thuốc trong dịch vụ tồn không?
    @api.onchange('therapy_prescription_line_remain_ids')
    def therapy_prescription_line_remain_onchange(self):
        if self.therapy_prescription_line_remain_ids:
            self.get_medicine = False
            for therapy_prescription_line_remain_id in self.therapy_prescription_line_remain_ids.filtered(lambda line:line.qty != 0):
                if therapy_prescription_line_remain_id.product_id.x_is_medicine_day:
                    self.get_medicine = True

    @api.onchange('get_medicine')
    def get_medicine_onchange(self):
        if not self.get_medicine:
            self.therapy_prescription_line_medicine_ids = False

    @api.model
    def default_get(self, fields):
        res = super(TherapyPrescription, self).default_get(fields)
        res['user_id'] = self._context.get('uid')
        return res

    @api.multi
    def action_get_product_remain(self):
        for prescription in self:
            if not prescription.therapy_record_id.therapy_record_product_ids:
                raise UserError(_(
                "Hồ sơ trị liệu %s chưa có sản phẩm/ dịch vụ tồn!") % (prescription.therapy_record_id.name))
            arr_therapy_prescription_line_remain = []
            for therapy_record_product in prescription.therapy_record_id.therapy_record_product_ids:
                qty_available = therapy_record_product.qty_available
                if therapy_record_product.qty_max != -1:
                    if therapy_record_product.product_id.type == 'product':
                        moves = self.env['stock.move'].search(
                            [('x_therapy_record_id', '=', prescription.therapy_record_id.id),
                             ('product_id', '=', therapy_record_product.product_id.id),
                             ('x_is_product_remain', '=', True),
                             ('x_order_line_id', '=', therapy_record_product.order_line_id.id),
                             ('x_order_id', '=', therapy_record_product.order_id.id),
                             ('picking_id.state', 'not in', ['done', 'cancel'])])
                        if moves:
                            for move in moves:
                                qty_available -= move.product_uom_qty
                    if therapy_record_product.product_id.type == 'service':
                        using_lines = self.env['izi.service.card.using.line'].search(
                            [('therapy_record_id', '=', prescription.therapy_record_id.id),
                             ('service_id', '=', therapy_record_product.product_id.id),
                             ('x_order_line_id', '=', therapy_record_product.order_line_id.id),
                             ('x_order_id', '=', therapy_record_product.order_id.id),
                             ('using_id.state', 'not in', ['done', 'cancel'])])
                        if using_lines:
                            if therapy_record_product.product_id.x_is_massage:
                                arr_using = []
                                for using_line in using_lines:
                                    arr_using.append(using_line.using_id.id)
                                for using_id in set(arr_using):
                                    qty_product = len(using_lines.filtered(lambda line: line.using_id.id == using_id and line.x_order_id == therapy_record_product.order_id))
                                    arr_area = []
                                    for service_massage_id in using_lines.filtered(lambda line: line.using_id.id == using_id and line.x_order_id == therapy_record_product.order_id):
                                        arr_area.append(service_massage_id.body_area_ids[0])
                                    qty_area = len(set(arr_area))
                                    qty_available -= (qty_product/ qty_area)
                            else:
                                for using_line in using_lines:
                                    qty_available -= using_line.quantity
                arr_therapy_prescription_line_remain.append((0, 0, {
                    'product_id': therapy_record_product.product_id.id,
                    'qty': 0,
                    'qty_available': qty_available,
                    'uom_id': therapy_record_product.uom_id.id,
                    'note': '',
                    'type': 'remain',
                    'order_id': therapy_record_product.order_id.id,
                    'order_line_id': therapy_record_product.order_line_id.id,
                    'actual_debt': therapy_record_product.actual_debt,
                    'body_area_ids': therapy_record_product.body_area_ids
                }))
            prescription.therapy_prescription_line_remain_ids = False
            prescription.therapy_prescription_line_remain_ids = arr_therapy_prescription_line_remain

    def get_product_remain(self):
        check = False
        arr_product_remain = []
        for therapy_prescription_line_remain_id in self.therapy_prescription_line_remain_ids:
            if therapy_prescription_line_remain_id.qty != 0:
                if therapy_prescription_line_remain_id.product_id.type == 'product':
                    arr_product_remain.append({
                        'product_id': therapy_prescription_line_remain_id.product_id.id,
                        'qty': therapy_prescription_line_remain_id.qty,
                        'uom': therapy_prescription_line_remain_id.uom_id.id,
                        'x_is_product_remain': True,
                        'x_is_product_guarantee': False,
                        'order_line_id': therapy_prescription_line_remain_id.order_line_id.id,
                        'order_id': therapy_prescription_line_remain_id.order_id.id,
                        'note': therapy_prescription_line_remain_id.note,
                    })
                # lấy sản phẩm kèm theo của dịch vụ bắn để tạo đơn xuất kho
                if therapy_prescription_line_remain_id.product_id.include_product_id:
                    arr_product_remain.append({
                        'product_id': therapy_prescription_line_remain_id.product_id.include_product_id.id,
                        'qty': therapy_prescription_line_remain_id.qty,
                        'uom': therapy_prescription_line_remain_id.uom_id.id,
                        'x_is_product_remain': True,
                        'x_is_product_guarantee': False,
                        'order_line_id': therapy_prescription_line_remain_id.order_line_id.id,
                        'order_id': therapy_prescription_line_remain_id.order_id.id,
                        'note': therapy_prescription_line_remain_id.note,
                    })
                if therapy_prescription_line_remain_id.qty > therapy_prescription_line_remain_id.qty_available:
                    check = True
        return [arr_product_remain, check]

    def get_product_medicine(self):
        arr_product_medicine = []
        if self.therapy_prescription_line_medicine_ids:
            for therapy_prescription_line_medicine_id in self.therapy_prescription_line_medicine_ids:
                if therapy_prescription_line_medicine_id.qty != 0 and therapy_prescription_line_medicine_id.product_id.type != 'service':
                    arr_product_medicine.append({
                        'product_id': therapy_prescription_line_medicine_id.product_id.id,
                        'qty': therapy_prescription_line_medicine_id.qty,
                        'uom': therapy_prescription_line_medicine_id.uom_id.id,
                        'order_line_id': False,
                        'order_id': False,
                        'x_is_product_remain': False,
                        'x_is_product_guarantee': False,
                        'note': therapy_prescription_line_medicine_id.note,
                    })
        return arr_product_medicine

    def get_product_warranty(self):
        arr_product_warranty = []
        if self.therapy_prescription_line_warranty_ids:
            for therapy_prescription_line_warranty_id in self.therapy_prescription_line_warranty_ids:
                if therapy_prescription_line_warranty_id.qty != 0 and therapy_prescription_line_warranty_id.product_id.type != 'service':
                    arr_product_warranty.append({
                        'product_id': therapy_prescription_line_warranty_id.product_id.id,
                        'qty': therapy_prescription_line_warranty_id.qty,
                        'uom': therapy_prescription_line_warranty_id.uom_id.id,
                        'order_line_id': False,
                        'order_id': False,
                        'x_is_product_remain': False,
                        'x_is_product_guarantee': True,
                        'note': therapy_prescription_line_warranty_id.note,
                    })
                if therapy_prescription_line_warranty_id.product_id.include_product_id:
                    arr_product_warranty.append({
                        'product_id': therapy_prescription_line_warranty_id.product_id.include_product_id.id,
                        'qty': therapy_prescription_line_warranty_id.qty,
                        'uom': therapy_prescription_line_warranty_id.uom_id.id,
                        'x_is_product_remain': True,
                        'x_is_product_guarantee': False,
                        'order_line_id': therapy_prescription_line_warranty_id.order_line_id.id,
                        'order_id': therapy_prescription_line_warranty_id.order_id.id,
                        'note': therapy_prescription_line_warranty_id.note,
                    })
        return arr_product_warranty

    def get_service_remain(self):
        check = False
        arr_service_remain = []
        for therapy_prescription_line_remain_id in self.therapy_prescription_line_remain_ids:
            if therapy_prescription_line_remain_id.qty != 0 \
                    and not therapy_prescription_line_remain_id.product_id.x_is_medicine_day \
                    and therapy_prescription_line_remain_id.product_id.product_tmpl_id.type == 'service':
                arr_service_remain.append({
                    'product_id': therapy_prescription_line_remain_id.product_id.id,
                    'qty': therapy_prescription_line_remain_id.qty,
                    'uom': therapy_prescription_line_remain_id.uom_id.id,
                    'body_area_ids': [(6, 0, therapy_prescription_line_remain_id.body_area_ids.ids)],
                    'order_line_id': therapy_prescription_line_remain_id.order_line_id.id,
                    'order_id': therapy_prescription_line_remain_id.order_id.id,
                })
                if not therapy_prescription_line_remain_id.product_id.x_is_injection and therapy_prescription_line_remain_id.qty > therapy_prescription_line_remain_id.qty_available:
                    check = True
        return [arr_service_remain, check]

    def get_service_warranty(self):
        arr_product_warranty = []
        if self.therapy_prescription_line_warranty_ids:
            for therapy_prescription_line_warranty_id in self.therapy_prescription_line_warranty_ids:
                if therapy_prescription_line_warranty_id.qty != 0 and therapy_prescription_line_warranty_id.product_id.type == 'service':
                    arr_product_warranty.append({
                        'product_id': therapy_prescription_line_warranty_id.product_id.id,
                        'qty': therapy_prescription_line_warranty_id.qty,
                        'uom': therapy_prescription_line_warranty_id.uom_id.id,
                        'body_area_ids': [(6, 0, therapy_prescription_line_warranty_id.body_area_ids.ids)],
                        'x_is_product_guarantee': True,
                        'order_line_id': False,
                        'order_id': False,
                    })
        return arr_product_warranty

    def create_stock_picking(self, arr_product_stocks, product_medicine_boolean):
        x_medicine_day_ok = False
        Picking = self.env['stock.picking']
        Move = self.env['stock.move']
        StockWarehouseObj = self.env['stock.warehouse']
        picking_type_id = self.env.user.x_pos_config_id.picking_type_id
        if not picking_type_id:
            raise UserError(_('Chưa cấu hình loại điều chuyển kho cho điểm bán hàng của bạn!'))
        if self.partner_id:
            destination_id = self.partner_id.property_stock_customer.id
        else:
            if (not picking_type_id) or (not picking_type_id.default_location_dest_id):
                customerloc, supplierloc = StockWarehouseObj._get_partner_locations()
                destination_id = customerloc.id
            else:
                destination_id = picking_type_id.default_location_dest_id.id
        if product_medicine_boolean:
            x_medicine_day_ok = True
        if arr_product_stocks:
            picking_vals = {
                'origin': self.name,
                'partner_id': self.partner_id.id,
                'scheduled_date': fields.Datetime.now(),
                'picking_type_id': picking_type_id.id,
                'move_type': 'direct',
                'location_id': picking_type_id.default_location_src_id.id,
                'location_dest_id': destination_id,
                'x_therapy_prescription_id': self.id,
                'x_medicine_day_ok': x_medicine_day_ok,
            }
            picking_id = Picking.create(picking_vals)
            for arr_product_stock in arr_product_stocks:
                Move.create({
                    'name': self.name,
                    'product_uom': arr_product_stock['uom'],
                    'picking_id': picking_id.id,
                    'picking_type_id': picking_type_id.id,
                    'product_id': arr_product_stock['product_id'],
                    'product_uom_qty': arr_product_stock['qty'],
                    'location_id': picking_type_id.default_location_src_id.id,
                    'location_dest_id': destination_id,
                    'x_therapy_prescription_id': self.id,
                    'x_is_product_remain': arr_product_stock['x_is_product_remain'],
                    'x_is_product_guarantee': arr_product_stock['x_is_product_guarantee'],
                    'x_order_line_id': arr_product_stock['order_line_id'],
                    'x_order_id': arr_product_stock['order_id'],
                    'note': arr_product_stock['note'],
                })
        self.state_picking = 'open'


    def create_use_service(self, arr_service_remain):
        use_service_card = self.env['izi.service.card.using']
        use_service_card_line = self.env['izi.service.card.using.line']
        Product_Obj = self.env['product.product']
        arr_warranty_products = self.get_service_warranty()
        session = self.env['pos.session'].search(
            [('state', '=', 'opened'), ('config_id', '=', self.user_id.x_pos_config_id.id)],
            limit=1)
        if arr_service_remain:
            use_service_card_id = use_service_card.create({
                'type': 'bundle',
                'customer_id': self.partner_id.id,
                'redeem_date': fields.Datetime.now(),
                'state': 'draft',
                'user_id': self.user_id.id,
                'pos_session_id': session.id,
                'therapy_prescription_id': self.id,
                'pricelist_id': self.partner_id.property_product_pricelist.id,
            })
            for service in arr_service_remain:
                product_id = Product_Obj.search([('id', '=', service['product_id'])])
                if product_id.x_is_massage:
                    qty = 1
                    while qty <= service['qty']:
                        for body_area in service['body_area_ids'][0][2]:
                            use_service_card_line.create({
                                'type': 'service_bundle',
                                'service_id': service['product_id'],
                                'quantity': 1,
                                'using_id': use_service_card_id.id,
                                'body_area_ids': [(6, 0, [body_area])],
                                'therapy_prescription_id': self.id,
                                'x_order_line_id': service['order_line_id'],
                                'x_order_id': service['order_id'],
                            })
                        qty += 1
                else:
                    use_service_card_line.create({
                        'type': 'service_bundle',
                        'service_id': service['product_id'],
                        'quantity': service['qty'],
                        'using_id': use_service_card_id.id,
                        'body_area_ids': service['body_area_ids'],
                        'therapy_prescription_id': self.id,
                        'x_order_line_id': service['order_line_id'],
                        'x_order_id': service['order_id'],
                    })
        if arr_warranty_products:
            use_service_card_id = use_service_card.create({
                'type': 'guarantee_bundle',
                'customer_id': self.partner_id.id,
                'redeem_date': fields.Datetime.now(),
                'state': 'draft',
                'user_id': self.user_id.id,
                'pos_session_id': session.id,
                'therapy_prescription_id': self.id,
                'pricelist_id': self.partner_id.property_product_pricelist.id,
            })
            for product in arr_warranty_products:
                product_id = Product_Obj.search([('id', '=', product['product_id'])])
                if product_id.x_is_massage:
                    qty = 1
                    while qty <= product['qty']:
                        for body_area in product['body_area_ids'][0][2]:
                            use_service_card_line.create({
                                'type': 'service_card1',
                                'service_id': product['product_id'],
                                'quantity': 1,
                                'using_id': use_service_card_id.id,
                                'body_area_ids': [(6, 0, [body_area])],
                                'therapy_prescription_id': self.id,
                                'x_order_line_id': product['order_line_id'],
                                'x_order_id': product['order_id'],
                            })
                        qty += 1
                else:
                    use_service_card_line.create({
                        'type': 'service_card1',
                        'service_id': product['product_id'],
                        'quantity': product['qty'],
                        'using_id': use_service_card_id.id,
                        'body_area_ids': product['body_area_ids'],
                        'therapy_prescription_id': self.id,
                        'x_order_line_id': product['order_line_id'],
                        'x_order_id': product['order_id'],
                    })
        self.state_using = 'open'

    @api.multi
    def send_prescription(self):
        for prescription in self:
            if prescription.state != 'draft':
                raise UserError('Trạng thái của Phiếu chỉ định đã thay đổi. Vui lòng F5 để tiếp tục thao tác!')
            # # todo kiểm tra nếu có chọn ngày thuốc mà k xuất thuốc thì cảnh báo
            self.therapy_prescription_line_remain_onchange()
            if self.get_medicine and len(self.get_product_medicine()) == 0:
                raise UserError(_('Không có số lượng của sản phẩm thuốc khi chỉ định ngày thuốc'))
            if not self.get_medicine and len(self.get_product_medicine()) != 0:
                raise UserError(_('Phải chỉ định ngày thuốc mới được xuất sản phẩm thuốc'))
            # todo kiểm tra trước khi xác nhận
            # khong được bỏ trống các danh mục trên phiếu chỉ định
            if not prescription.therapy_prescription_line_remain_ids and not prescription.therapy_prescription_line_warranty_ids and not prescription.therapy_prescription_line_medicine_ids:
                raise UserError(_('Chưa lựa chọn Sản phẩm/Dịch vụ sử dụng'))
            arr_product_remain, check_product_stock = prescription.get_product_remain()
            arr_product_medicine = self.get_product_medicine()
            arr_product_stocks = arr_product_medicine + arr_product_remain + self.get_product_warranty()
            if len(arr_product_stocks) > 0:
                prescription.is_create_stock_picking = True
            arr_service_remain, check_use_service = prescription.get_service_remain()
            # cảnh báo khi đã tính toán sp/ dv tồn mà k chọn số lượng sử dụng và 2 danh mục thuốc và bảo hành cũng trống
            if not arr_product_remain and not arr_service_remain and not prescription.therapy_prescription_line_warranty_ids and not prescription.therapy_prescription_line_medicine_ids:
                raise UserError(_('Chưa lựa chọn Sản phẩm/Dịch vụ sử dụng'))
            # lấy dv cần tạo đơn sddv
            arr_service_remain = self.get_service_remain()[0]
            if check_use_service:
                prescription.state = 'waiting'
                pass
            elif check_product_stock and not check_use_service:
                # tạo đơn sử dụng dịch vụ
                self.create_use_service(arr_service_remain)
                prescription.state = 'waiting'
                pass
            else:
                # tạo đơn sử dụng dịch vụ
                self.create_use_service(arr_service_remain)
                if prescription.is_create_stock_picking:
                    prescription.state = 'transfer_confirmation'
                    prescription.action_unlink()
                else:
                    prescription.action_approve()
                    prescription.action_unlink()

    def action_done(self):
        arr_service_remain, check_use_service = self.get_service_remain()
        if check_use_service:
            self.create_use_service(arr_service_remain)
        #nếu có sp cần xuất kho thì chuyển sang trạng thái chờ xác nhận của kế toán quầy
        if self.is_create_stock_picking:
            self.state = 'transfer_confirmation'
        else:
            self.action_approve()
        self.action_unlink()

    @api.multi
    def action_approve(self):
        for prescription in self:
            if prescription.state == 'confirm':
                raise UserError('Phiếu chỉ định đã được xác nhận. Vui lòng ấn F5 để thao tác tiếp!')
            # lấy sp cần tạo đơn xuất kho
            arr_product_remain = prescription.get_product_remain()[0]
            arr_product_medicine = prescription.get_product_medicine()
            if arr_product_medicine:
                product_medicine_boolen = True
            else:
                product_medicine_boolen = False
            arr_product_stocks = arr_product_medicine + arr_product_remain + prescription.get_product_warranty()
            #tạo đơn xuất kho
            a = self.create_stock_picking(arr_product_stocks, product_medicine_boolen)
            prescription.state = 'confirm'

    def action_cancel(self):
        if self.state == 'cancel':
            raise UserError("Phiếu chỉ định cho hồ sơ %s của khách hàng [%s] %s đã được hủy vui lòng tải lại trang để cập nhật trạng thái của phiếu." % (str(self.therapy_record_id.name), str(self.partner_id.x_old_code), str(self.partner_id.name)))
        #todo hủy đơn sử dụng dịch vụ
        ObjUsingLine = self.env['izi.service.card.using.line']
        for service_card_using_id in self.izi_service_card_using_ids.filtered(lambda sc: sc.state != 'cancel'):
            if service_card_using_id.state in ['wait_approve','wait_payment']:
                service_card_using_id.action_back()
            elif service_card_using_id.state == 'wait_material':
                service_card_using_id.action_cancel()
            else:
                #cap nhat trạng thái của line và giường trong line
                for service_using_line in ObjUsingLine.search([('using_id', '=', service_card_using_id.id)]):
                    if service_using_line.state == 'new':
                        continue
                    else:
                        service_using_line.state = 'new'
                        for bed in service_using_line.bed_ids:
                            bed.state = 'ready'
                service_card_using_id.option_refund = 'cancel'
                service_card_using_id.process_refund()
            service_card_using_id.state == 'cancel'
        #todo hủy đơn trả hàng và đơn nhập kho
        for prescription_refund in self.therapy_prescription_return_product_line_ids:
            if prescription_refund.therapy_prescription_return_product_id.picking_id.state == 'waiting_warehouse':
                prescription_refund.therapy_prescription_return_product_id.picking_id.action_cancel()
            elif prescription_refund.therapy_prescription_return_product_id.picking_id.state == 'done':
                user = self.env['res.users'].search([('id', '=', self._uid)])
                if not user.has_group('stock_picking_cancel.group_stock_picking_cancel'):
                    raise UserError('Nhân viên %s không có quyền hủy đơn nhập kho! Vui lòng liên lạc với quản lý để được xử lý' %(user.name))
                prescription_refund.therapy_prescription_return_product_id.picking_id.action_cancel_picking()
            prescription_refund.state = 'cancel'
            if prescription_refund.therapy_prescription_return_product_id.state != 'cancel':
                prescription_refund.therapy_prescription_return_product_id.state = 'cancel'
        #todo hủy đơn xuất kho
        for stock_picking in self.stock_picking_ids.filtered(lambda sp: sp.state != 'cancel'):
            if stock_picking.state != 'done':
                stock_picking.action_cancel()
            else:
                user = self.env['res.users'].search([('id', '=', self._uid)])
                if not user.has_group('stock_picking_cancel.group_stock_picking_cancel'):
                    raise UserError(
                        'Nhân viên %s không có quyền hủy đơn nhập kho! Vui lòng liên lạc với quản lý để được xử lý' % (
                            user.name))
                #cập nhật lại số lượng đã sử dụng của sp trong tồn hstl
                for move_line in stock_picking.move_lines.filtered(lambda move: move.quantity_done != 0):
                    qty_move = move_line.quantity_done
                    for record_product_id in self.therapy_record_id.therapy_record_product_ids.filtered(
                            lambda remain: remain.product_id.id == move_line.product_id.id):
                        qty_prescription = 0
                        for product_prescription in self.env['therapy.prescription.line'].search(
                                [('product_id', '=', record_product_id.product_id.id),
                                 ('order_id', '=', record_product_id.order_id.id),
                                 ('therapy_prescription_id', '=', self.id),
                                 ('type', '!=', 'guarantee')]):
                            if product_prescription.order_line_id == record_product_id.order_line_id:
                                qty_prescription = product_prescription.qty
                        if qty_prescription == 0:
                            continue
                        if qty_move <= qty_prescription:
                            record_product_id.qty_used = record_product_id.qty_used - qty_move
                            continue
                        else:
                            record_product_id.qty_used = record_product_id.qty_used - qty_prescription
                            qty_move -= qty_prescription
                # todo cộng tồn số ngày thuốc
                record_product_medicine_ids = self.therapy_record_id.therapy_record_product_ids.filtered(
                    lambda remain: remain.product_id.x_is_medicine_day)
                for record_product_medicine_id in record_product_medicine_ids:
                    qty = 0
                    if record_product_medicine_id and stock_picking.x_medicine_day_ok:
                        for line_remain_id in self.therapy_prescription_line_remain_ids.filtered(
                                lambda
                                        line: line.product_id.x_is_medicine_day and line.product_id.id == record_product_medicine_id.product_id.id):
                            if line_remain_id.order_line_id.id == record_product_medicine_id.order_line_id.id and line_remain_id.order_id.id == record_product_medicine_id.order_id.id:
                                qty += line_remain_id.qty
                        record_product_medicine_id.qty_used -= qty

                # for therapy_record_product_id in self.therapy_record_id.therapy_record_product_ids:
                #     therapy_quantity_used = 0
                #     for move_line in stock_picking.move_lines.filtered(lambda move_line:move_line.quantity_done !=0 and move_line.product_id.id == therapy_record_product_id.product_id.id and move_line.x_order_id.id == therapy_record_product_id.order_id.id and move_line.x_order_line_id.id == therapy_record_product_id.order_line_id.id):
                #         if move_line.x_is_product_remain or move_line.x_is_product_guarantee:
                #             therapy_quantity_used += move_line.quantity_done
                #     therapy_record_product_id.qty_used -= therapy_quantity_used
                #
                #     if therapy_record_product_id.product_id.x_is_medicine_day and stock_picking.x_medicine_day_ok:
                #         medicine_day = 0
                #         for line_remain_id in self.therapy_prescription_line_remain_ids.filtered(
                #                 lambda
                #                         line: line.product_id.x_is_medicine_day and line.product_id.id == therapy_record_product_id.product_id.id):
                #             if line_remain_id.order_line_id.id == therapy_record_product_id.order_line_id.id and line_remain_id.order_id.id == therapy_record_product_id.order_id.id:
                #                 medicine_day += line_remain_id.qty
                #         therapy_record_product_id.qty_used -= medicine_day
                stock_picking.action_cancel_picking()


        self.state = 'cancel'

    @api.multi
    def action_unlink(self):
        for prescription in self:
            for therapy_prescription_line_remain_id in prescription.therapy_prescription_line_remain_ids:
                if therapy_prescription_line_remain_id.qty == 0:
                    therapy_prescription_line_remain_id.unlink()


    @api.multi
    def unlink(self):
        for prescription in self:
            if prescription.state != 'draft':
                raise UserError("Phiếu chỉ định khác trạng thái khóa nên không được phép xóa!")
            else:
                return super(TherapyPrescription, self).unlink()


class PrescriptionTaskLine(models.Model):  # Phiếu chỉ định Line
    _name = 'therapy.prescription.line'

    name = fields.Char('Therapy prescription line')
    therapy_prescription_id = fields.Many2one('therapy.prescription', 'Therapy prescription')
    type = fields.Selection(
        [('warranty', 'Warranty'), ('remain', 'Remain'), ('medicine', 'Medicine')], string='Type')
    product_id = fields.Many2one('product.product', 'Product')
    uom_id = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure', readonly=True)
    qty = fields.Float(string='Quantity')  # Số lượng
    qty_available = fields.Float(string='Quantity available')  # SỐ lượng khả dụng
    qty_reserved = fields.Float(string='Quantity Reserved')
    qty_therapy = fields.Float(string='Quantity Therapy')
    price_unit = fields.Float(string='Price unit', default=0)
    amount = fields.Float(string='Amount', default=0)
    note = fields.Char(string='Note')
    body_area_ids = fields.Many2many('body.area', string='Body Area')
    product_is_massage = fields.Boolean(related='product_id.x_is_massage', string='Product Is Massage', readonly=1,
                                        store=True)
    product_is_injection = fields.Boolean(related='product_id.x_is_injection', string='Product Is Injection',
                                          readonly=1, store=True)
    actual_debt = fields.Float(string='Actual Debt')
    order_id = fields.Many2one('pos.order', string='Order')
    order_line_id = fields.Many2one('pos.order.line', string='Line Order')

    @api.onchange('product_id', 'qty')
    def _onchange_product_qty(self):
        for line in self:
            prescription_id = line.therapy_prescription_id
            if not line.product_id.x_is_massage and not line.product_id.x_is_medicine_day and line.product_id.type == 'product' or line.product_id.include_product_id:
                if line.product_id.include_product_id:
                    product_id = line.product_id.include_product_id
                else:
                    product_id = line.product_id
                total_availability = self.env['stock.quant']._get_available_quantity(product_id, prescription_id.location_id)
                warning_mess = {
                    'title': _('Cảnh báo!'),
                    'message': _('Sản phẩm "' + str(
                        product_id.product_tmpl_id.name) + '" chỉ còn ' + str(
                        total_availability)) + ' trong ' + str(prescription_id.location_id.name)
                }
                if line.qty > total_availability:
                    return {'warning': warning_mess}
            if line.qty < 0:
                    raise UserError('Không được phép nhập số lượng âm! Vui lòng nhập lại.')
            if self.product_id.x_is_medicine_day:
                self.therapy_prescription_id.get_medicine = True
