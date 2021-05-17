# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date as my_date
import math


class PosOrder(models.Model):
    _inherit = 'pos.order'

    x_therapy_record_id = fields.Many2one('therapy.record', string='Therapy Record')
    x_categ_id = fields.Many2one('product.category', related='x_therapy_record_id.categ_id', string='Category', readonly=True)
    x_is_use_barem = fields.Boolean(default=False, string='Is use barem')
    x_pos_order_complement_ids = fields.One2many('pos.order.complement', 'pos_order_id', string='Pos Order Complement')
    x_barem_id = fields.Many2one('therapy.bundle.barem', string='Barem')
    x_is_create_therapy_record = fields.Boolean(string="Is create therapy record", default=False)

    @api.onchange('lines')
    def onchange_lines(self):
        check_is_therapy_record = False
        check_is_use_barem = False
        arr_body = []
        for order_line_id in self.lines:
            if order_line_id.x_categ_id.x_is_therapy_record:
                check_is_therapy_record = True
            if order_line_id.x_categ_id.x_is_use_barem:
                check_is_use_barem = True
        self.x_is_create_therapy_record = check_is_therapy_record
        self.x_is_use_barem = check_is_use_barem


    @api.multi
    def action_compute_barem(self):
        for order in self:
            #Kiểm tra đơn hàng có bán nhiều loại sp không?
            #Tính toán buổi massage
            order.x_pos_order_complement_ids = False
            if not order.lines: raise UserError("Chưa có sản phẩm để tính toán!")
            host_product = order.lines[0].product_id
            arr_categ = []
            for line in order.lines:
                if line.x_categ_id.x_is_use_barem and arr_categ.count(line.x_categ_id.id) == 0:
                    arr_categ.append(line.x_categ_id.id)
                if line.product_id.categ_id.x_is_therapy_record and not line.x_body_area_ids:
                    raise UserError("Chưa có vùng cơ thể đối với sản phẩm %s!" %(line.product_id.name))

            #Tìm kiếm barem
            #Lấy sp/dv của barem đổ vào sp bổ trợ
            for category_id in set(arr_categ):
                #tính tổng tiền và số vùng theo nhóm sp
                amount_total = 0
                arr_body_area = []
                for order_line in order.lines.filtered(lambda line:line.x_categ_id.id == category_id):
                    amount_total += order_line.price_subtotal_incl
                    arr_body_area += order_line.x_body_area_ids.ids
                count_area = len(set(arr_body_area))
                #tính số lượng 1 số sản phẩm theo công thức
                number_massage = int((amount_total * 1.2)/(1600000 * count_area)) + 1# = (giá trị tiền thanh toán mua tinh chất maxthin * 1,2) / ( 1.600.000 * số vùng )
                number_medicine = int(amount_total/1000000)# - Cứ 1 triệu tiền thanh toán tinh chất maxthin thì hỗ trợ 1 ngày thuốc mang về
                number_liposonic = int(amount_total/25000000) + 1# - Cứ 25 triệu thì hỗ trợ 1 lần
                number_dan_thai_doc = int(amount_total/25000000)# - Cứ 25 triệu thì hỗ trợ 1 lần
                number_dich_vu_khac = int(amount_total/25000000)#
                '''
                Kiểu cũ
                if amount_total < 15000000:
                    number_medicine = 0
                elif amount_total >= 15000000 and amount_total < 25000000:
                    number_medicine = 30
                else:
                    number_medicine = int((10 + (0.1 * (amount_total / 100000))))'''

                barem = order.env['therapy.bundle.barem'].search([('value_bundle_min', '<=', amount_total),
                                                                  ('value_bundle_max', '>', amount_total),
                                                                  ('categ_id', '=', category_id)], limit=1)
                category = self.env['product.category'].search([('id', '=', category_id)], limit=1)
                if not category: raise UserError("Không tìm thấy nhóm dịch vụ có id: %s" % (str(category_id)))
                if not barem: raise UserError("Không tìm thấy barem cho nhóm dịch vụ %s phù hợp với giá trị đơn hàng (%s). Vui lòng kiểm tra lại!" % (str(category.name), str(amount_total)))
                arr_pos_order_complement = []
                for barem_component_id in barem.therapy_bundle_barem_component_ids:

                    check = False
                    option_id = barem_component_id.option_ids[0]
                    if barem_component_id.qty == -1:

                        if option_id.product_id.default_code == 'DV0041':#Dịch vụ [DV0041] Liposonic
                            arr_pos_order_complement.append((0, 0, {
                                'component_id': barem_component_id.id,
                                'product_id': option_id.product_id.id,
                                'qty': number_liposonic,
                                'qty_max': number_liposonic,
                                'barem_id': barem.id,
                                'categ_id': barem.categ_id.id,
                            }))
                        elif option_id.product_id.default_code == 'DV0018':#Dịch vụ [DV0018] Dẫn thải độc GC toàn thân
                            arr_pos_order_complement.append((0, 0, {
                                'component_id': barem_component_id.id,
                                'product_id': option_id.product_id.id,
                                'qty': number_dan_thai_doc,
                                'qty_max': number_dan_thai_doc,
                                'barem_id': barem.id,
                                'categ_id': barem.categ_id.id,
                            }))
                        elif option_id.product_id.x_is_medicine_day:
                            arr_pos_order_complement.append((0, 0, {
                                'component_id': barem_component_id.id,
                                'product_id': option_id.product_id.id,
                                'qty': number_medicine,
                                'qty_max': number_medicine,
                                'barem_id': barem.id,
                                'categ_id': barem.categ_id.id,
                            }))
                        elif option_id.product_id.x_is_massage:
                            arr_pos_order_complement.append((0, 0, {
                                'component_id': barem_component_id.id,
                                'product_id': option_id.product_id.id,
                                'qty': number_massage,
                                'qty_max': number_massage,
                                'barem_id': barem.id,
                                'categ_id': barem.categ_id.id,
                            }))
                        else:
                            raise UserError("Sản phẩm/Dịch vụ [%s] %s đang được cấu hình trong barem %s nhưng chưa có quy định về công thức bổ trợ. Vui lòng liên hệ Admin để giải quyết!"
                                            % (str(option_id.product_id.default_code), str(option_id.product_id.name), str(barem.name)))
                    else:
                        arr_pos_order_complement.append((0, 0, {
                            'component_id': barem_component_id.id,
                            'product_id': option_id.product_id.id,
                            'qty': (barem_component_id.qty > 0) and barem_component_id.qty or 0,
                            'qty_max': barem_component_id.qty,
                            'barem_id': barem.id,
                            'categ_id': barem.categ_id.id,
                        }))
                order.write({
                    'x_pos_order_complement_ids': arr_pos_order_complement,
                })

    @api.multi
    def action_compute_massage(self):
        view = self.env.ref('izi_pos_bundle_therapy.pos_order_compute_massage_formview')

        amount_total = 0
        for order_line in self.lines:
            if order_line.x_use_compute_massage:
                amount_total += order_line.price_subtotal_incl
        compute_massage = self.env['pos.order.compute.massage'].create({
            'order_id': self.id,
            'amount_total': amount_total,
        })
        return {
            'name': _('Tính toán buổi giảm béo'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order.compute.massage',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': compute_massage.id,
            'context': self.env.context,
        }

    @api.multi
    def action_order_cancel(self):
        res = super(PosOrder, self).action_order_cancel()
        for order in self:
            order.x_pos_order_complement_ids = False
        return res

    def check_order_discount(self):
        self.ensure_one()
        if self.lines and not self.x_pos_partner_refund_id:
            # Lấy điểm bán hàng theo phiên trên đơn hàng
            try:
                pos_id = self.session_id.config_id.id
            except:
                raise UserError("Session must be opened before promotion calculating is execute!")
            # Kiểm tra nếu có chương trình KH đang hoạt động
            # today = date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
            # active_promo = self.env['pos.promotion'].search([('state', '=', 'activated'), ('pos_id', '=', pos_id),
            #                                                  ('date_start', '<=', today), ('date_end', '>=', today)])
            if not self.pricelist_id:
                raise UserError(
                    _('You have to select a pricelist in the form !\n'
                      'Please set one before choosing a product.'))
            product_obj = self.env['product.product']
            # Tổng số các sản phẩm chọn mua bao gồm sản phẩm lặp
            to_buy_product_dict = {}
            to_buy_product_ids = []
            # Số lượng thực xuất của các dòng quà tặng
            gift_real_out_dict = {}
            # Loại bỏ các sản phẩm là quà, các giảm giá, khuyến mãi đã tính trước đó (NẾU CÓ)
            for line in self.lines:
                if line.x_is_gift:
                    gift_real_out_dict[line.product_id.id] = line.x_qty
                    line.unlink()
                elif line.product_id.default_code and line.product_id.default_code.upper() == 'COIN':
                    # line.x_discount = 0
                    # line.discount = 0
                    # if line.product_id not in self.session_id.config_id.product_edit_price_ids:
                    #     line.price_unit = self.pricelist_id.get_product_price(line.product_id, 1.0, self.partner_id)
                    to_buy_product_ids.append(line.product_id.id)
                    if line.product_id.id in to_buy_product_dict:
                        to_buy_product_dict[line.product_id.id] += line.qty
                    else:
                        to_buy_product_dict[line.product_id.id] = line.qty
                elif not (line.product_id.default_code and line.product_id.default_code.upper() == 'PDDV'):
                    # line.x_discount = 0
                    # line.discount = 0
                    # if line.product_id not in self.session_id.config_id.product_edit_price_ids:
                    #     line.price_unit = self.pricelist_id.get_product_price(line.product_id, line.qty, self.partner_id)
                    to_buy_product_ids.append(line.product_id.id)
                    if line.product_id.id in to_buy_product_dict:
                        to_buy_product_dict[line.product_id.id] += line.qty
                    else:
                        to_buy_product_dict[line.product_id.id] = line.qty

            to_buy_product_dict2 = dict(to_buy_product_dict)
            to_buy_product_dict3 = dict(to_buy_product_dict)
            # ngoant xu ly doan chap thuan ctkm neu ban duoi gia
            # xử lý field x_custom_discount cho từng line
            for line in self.lines:
                price = self.pricelist_id.get_product_price(line.product_id, line.qty or 1.0, self.partner_id)
                if (line.price_unit * line.qty - line.x_discount) * (100 - line.discount) / 100 < price:
                    line.x_custom_discount = False
            # Nếu có chương trình khuyến mại -> thực hiện tính khuyến mại
            if self.x_promotion_id:
                # Các áp dụng khuyến mại và số lượng được chấp nhận
                to_promo_action_dict = {}
                partner_obj = self.env['res.partner']
                # Tất cả các áp dụng trong ctkm
                promo_actions = {}
                # Tính chiết khấu theo ctkm
                applied_records = []
                for line in self.x_promotion_id.line_ids:
                    # Số điều kiện đạt
                    pass_rule = 0
                    # Số lần áp dụng khuyến mại
                    count_action_apply = 0
                    # Xác định các điều kiện áp dụng KM
                    for rule in line.rule_ids:
                        try:
                            rule_domain = eval(rule.domain)
                        except Exception as e:
                            raise UserError("Some of rules to apply promotion are invalid! %s" % str(e))

                        # Loại trừ các mã DV đặc biệt
                        for domain in rule_domain:
                            if domain[0] == 'type' and domain[1] == '=' and domain[2] == 'service':
                                rule_domain.append(
                                    ['default_code', 'not in', ['COIN', 'PDDV', 'DISCOUNT', 'VDISCOUNT', 'PHOI']])

                        # Loại các chương trình áp dụng 1 lần đã áp dụng cho KH mua đơn
                        if line.apply_once and self.partner_id.id in line.applied_partner_ids.ids:
                            continue

                        # Nếu điều kiện áp dụng cho sản phẩm
                        if rule.type == 'product':
                            # Lấy các sản phẩm theo điều kiện
                            rule_domain.append(['id', 'in', to_buy_product_ids])
                            try:
                                mapped_rule_products = product_obj.search(rule_domain)
                            except:
                                raise UserError("Some of product rules to apply promotion are invalid!")
                            if len(mapped_rule_products):
                                mapped_product_count = {}
                                f = True
                                for mapped_product in mapped_rule_products:
                                    if mapped_product.id in to_buy_product_dict and to_buy_product_dict[
                                        mapped_product.id] >= rule.count:
                                        mapped_product_count[mapped_product.id] = to_buy_product_dict[mapped_product.id]
                                    else:
                                        f = False
                                if f:
                                    if rule.count != 0:
                                        lowest = None
                                        for i in mapped_product_count:
                                            count_action = 1 if rule.count == -1 else math.floor(
                                                mapped_product_count[i] / rule.count)
                                            if not lowest or count_action < lowest:
                                                lowest = count_action
                                                to_buy_product_dict3[
                                                    i] -= 0 if rule.count == -1 else lowest * rule.count
                                            else:
                                                to_buy_product_dict3 = dict(to_buy_product_dict)
                                        count_action_apply = lowest or 0
                                    pass_rule += 1

                        # Nếu điều kiện áp dụng cho KH
                        elif rule.type == 'partner':
                            try:
                                mapped_partner = partner_obj.search(rule_domain)
                            except:
                                raise UserError("Partner rule to apply promotion is invalid!")
                            # Nếu KH không thuộc điều kiện KM => Chuyển qua dòng KM khác
                            if self.partner_id.id not in mapped_partner.ids:
                                continue
                            else:
                                pass_rule += 1
                                if pass_rule == len(line.rule_ids) and not count_action_apply:
                                    count_action_apply = 1
                    # Nếu số điều kiện đạt = số điều kiện km => thực hiện action
                    if pass_rule == len(line.rule_ids) and count_action_apply:
                        if line.apply_once:
                            applied_records.append(line.id)
                        to_buy_product_dict = dict(to_buy_product_dict3)
                        for actition_id in line.action_ids:
                            if actition_id.id not in to_promo_action_dict:
                                to_promo_action_dict[actition_id.id] = count_action_apply
                                promo_actions[actition_id.id] = actition_id
                            else:
                                to_promo_action_dict[actition_id.id] += count_action_apply
                # Ghi lại các dòng khuyến mại được chấp nhận
                if len(applied_records):
                    self.x_applied_promo = ','.join(map(str, applied_records))
                # Nếu có các áp dụng KM
                if len(to_promo_action_dict):
                    gift_products = {}  # Tặng quà
                    fixed_price_product_dict = {}  # Giá cố định
                    discount_percent = 0.0  # Giảm %
                    discount_amount = 0.0  # Giảm số tiền cụ thể
                    discount_amount_product_dict = {}

                    # Cộng dồn các khuyến mại
                    for action in to_promo_action_dict:
                        if not promo_actions[action].active: continue
                        if promo_actions[action].type == 'gift':
                            # Thêm các sản phẩm được tặng
                            for p in promo_actions[action].line_ids:
                                if p.product_id.id in gift_products:
                                    gift_products[p.product_id.id] += to_promo_action_dict[action] * p.product_qtt
                                else:
                                    gift_products[p.product_id.id] = to_promo_action_dict[action] * p.product_qtt
                        elif promo_actions[action].type == 'discount_amount':
                            if promo_actions[action].product_id.id in discount_amount_product_dict:
                                discount_amount_product_dict[promo_actions[action].product_id.id] += \
                                to_promo_action_dict[action] * promo_actions[action].discount
                            else:
                                discount_amount_product_dict[promo_actions[action].product_id.id] = \
                                to_promo_action_dict[action] * promo_actions[action].discount
                        elif promo_actions[action].type == 'discount_percent':
                            discount_percent += promo_actions[action].discount
                        elif promo_actions[action].type == 'fixed_price':
                            for p in promo_actions[action].line_ids:
                                fixed_price_product_dict[p.product_id.id] = p.product_price
                return gift_products, fixed_price_product_dict, discount_percent, discount_amount, discount_amount_product_dict

    @api.multi
    def action_send_payment(self):
        count = 0
        count_massage = 0
        ProductLot_Obj = self.env['stock.production.lot']
        PosOrderLine = self.env['pos.order.line']
        for order in self:
            if order.x_is_use_barem:
                categ_id = order.lines[0].x_categ_id
                if not order.lines.filtered(lambda line:line.x_categ_id != categ_id):
                    self.action_compute_barem()
                else:
                    if not order.x_pos_order_complement_ids:
                        raise UserError(_("Bạn chưa tính toán và nhập sản phẩm bổ trợ cho gói liệu trình!"))
                    else:
                        product_complement_ids = order.x_pos_order_complement_ids
                        for product_complement_id in product_complement_ids:
                            if product_complement_id.qty_max != -1:
                                # count += product_complement_id.qty
                                if product_complement_id.qty > product_complement_id.qty_max:
                                    raise UserError(_(
                                        "Số lượng sản phẩm/ Dịch vụ %s bổ trợ vượt quá số lượng cho phép! %s/%s" % (
                                        str(product_complement_id.product_id.default_code), str(product_complement_id.qty),
                                        str(product_complement_id.qty_max))))
            if not order.lines:
                raise except_orm("Cảnh báo!", ('Đơn hàng bán đang không có sản phẩm hoặc dịch vụ'))
            if order.x_type == '3':  # Đơn hàng của đơn dịch vụ
                raise except_orm('Thông báo', 'Đơn hàng được sinh ra từ các đơn dịch vụ, vui lòng không thao tác ở đây!')

            if order.x_pos_partner_refund_id:
                order.state = 'to_payment'
            have_service = False
            have_card_service = False
            approve_price = False
            msg = []
            for line in order.lines.filtered(lambda line: not line.product_id.categ_id.x_is_therapy_record):
                if line.product_id.type == 'service' and line.product_id.x_type_card == 'none' and order.x_type != '2':
                    have_service = True
                if line.product_id.default_code == 'TDV':
                    have_card_service = True

            if have_service and not have_card_service:
                order._add_service_to_service_card()
            if approve_price:
                # do nothing
                '''
                '''
            else:
                if order.amount_total:
                    order.state = 'to_payment'
                else:
                    order.action_pos_order_paid()
            # todo kiểm tra slg khuyến mại có vượt quy định
            # gift_products, fixed_price_product_dict, discount_percent, discount_amount, discount_amount_product_dict = self.check_order_discount()
            for order_line in order.lines:
                # gắn voucher
                if order_line.product_id.product_tmpl_id.x_type_card == 'pmh':
                    product_lot_ids = ProductLot_Obj.search(
                        [('x_status', '=', 'actived'), ('product_id', '=', order_line.product_id.id)])
                    for product_lot_id in product_lot_ids:
                        check_lot = PosOrderLine.search([('lot_name', '=', product_lot_id.name.upper().strip())])
                        if len(check_lot) != 0:
                            continue
                        order_line.update({
                            'lot_name': product_lot_id.name.upper().strip(),
                        })
                        argvs_lot = {
                            'pos_order_line_id': order_line.id,
                            'lot_name': product_lot_id.name.upper().strip(),
                        }
                        pos_lot_id = self.env['pos.pack.operation.lot'].create(argvs_lot)
                        break
                    if not order_line.lot_name:
                        raise UserError(
                            'Không đủ mã Voucher để hoàn thành đơn hàng! Vui lòng phát hành thêm để hoàn thành đơn hàng')
                # check slg kmai
                # if order_line.x_is_gift:
                #     for product_gift_id in gift_products.keys():
                #         if product_gift_id == order_line.product_id and gift_products[product_gift_id] < order_line.qty:
                #             order.state = 'to_confirm'
                #             break
                    # for

    def _add_service_to_card(self, list, lot_obj):
        amount = 0
        amount_product = 0
        lines_lot = []
        for line in self.lines:
            if (line.product_id.product_tmpl_id.x_type_card != 'tdv') and (
                    line.product_id.product_tmpl_id.type != 'service'):
                amount_product += (line.price_subtotal_incl - line.x_discount)
            if line.product_id.product_tmpl_id.x_type_card == 'tdv':
                continue
            if line.product_id.product_tmpl_id.type != 'service':
                continue
            if line.product_id.default_code in list:
                continue
            if line.product_id.categ_id.x_is_therapy_record:
                continue
            argvs = {
                'lot_id': lot_obj.id,
                'product_id': line.product_id.id,
                'total_qty': line.qty,
                'qty_hand': line.qty,
                'qty_use': 0,
                'price_unit': line.price_unit - (line.price_unit * line.discount / 100) - (line.x_discount / line.qty),
                'remain_amount': line.price_subtotal_incl,
                'amount_total': line.price_subtotal_incl,
                'state': 'ready',
                'partner_id': self.partner_id.id
            }
            k = 0
            for i in range(len(lines_lot)):
                if lines_lot[i]['product_id'] == line.product_id.id:
                    k = k + 1
                    lines_lot[i]['total_qty'] = lines_lot[i]['total_qty'] + line.qty
            if k == 0:
                lines_lot.append(argvs)
            amount = amount + line.price_subtotal_incl
        return amount, lines_lot, amount_product

    def check_therapy_record(self):
        #kiểm tra các sp (trừ phí đổi trả và thẻ dịch vụ) có phải là dịch vụ cần gắn thẻ dịch vụ
        for order_line in self.lines.filtered(lambda line: not line.x_edit_price and line.product_id.tracking != 'serial' and line.product_id.id != self.config_id.x_charge_refund_id.id):
            if order_line.product_id.categ_id.x_is_therapy_record:
                return True
            else:
                return False

    def _product_order(self, category):
        products_order = []
        param_obj = self.env['ir.config_parameter']
        product_product_obj = self.env['product.product']
        for order_line in self.lines:
            #lấy ra sản phẩm kèm theo của dịch vụ ống
            # if not order_line.product_id.include_product_id:
            #     raise UserError('Dịch vụ %s chưa được cấu hình sản phẩm đi kèm!' % (str(order_line.product_id.default_code)))
            # product = order_line.product_id.include_product_id
            #lấy ra sản phẩn được bán trong tab lines theo nhóm sản phẩm
            if order_line.product_id.categ_id.id == category.id:
                products_order.append({
                    'product_id': order_line.product_id.id,
                    'uom_id': order_line.product_id.product_tmpl_id.uom_id.id,
                    'qty': order_line.qty,
                    'body_area_ids': order_line.x_body_area_ids.ids,
                    'order_id': self.id,
                    'order_line_id': order_line.id,
                    'price_unit': order_line.price_unit - (order_line.price_unit * order_line.discount / 100) - (order_line.x_discount / order_line.qty),
                    'price_subtotal_incl': order_line.price_subtotal_incl,
                })
            #lấy ra dịch vụ bắn tương ứng của sản phẩm ống từ thông số hệ thống
            # code = param_obj.get_param(product.default_code)
            # if not code:
            #     raise UserError(
            #         'Sản phẩm %s chưa được cấu hình dịch vụ bắn trong thông số hệ thống!' % (str(product.default_code)))
            # arr_code = code.split(',')
            # if len(arr_code) <= 0:
            #     raise UserError(
            #         'Sản phẩm %s chưa được cấu hình dịch vụ bắn trong thông số hệ thống!' % (str(product.default_code)))
            # for code in arr_code:
            #     product_injection = product_product_obj.search([('default_code', '=', code)], limit=1)
            #     if product_injection:
            #         products_order.append({
            #             'product_id': product_injection.id,
            #             'uom_id': product_injection.uom_id.id,
            #             'qty': -1,
            #             'body_area_ids': False,
            #         })
            # if len(products_order) <= 1:
            #     raise UserError(
            #         'Không tìm thấy dịch vụ bắn được cấu hình của sản phẩm %s!' % (str(product.default_code)))
        for order_complement in self.x_pos_order_complement_ids:
            if order_complement.barem_id.categ_id.id == category.id:
                products_order.append({
                    'product_id': order_complement.product_id.id,
                    'uom_id': order_complement.product_id.uom_id.id,
                    'qty': order_complement.qty,
                    'body_area_ids': [],
                    'order_id': self.id,
                    'order_line_id': False,
                    'price_unit': 0,
                    'price_subtotal_incl': 0,
                })
        return products_order

    def _create_therapy_bundle(self):
        # Tạo gói liệu trình
        therapy_bundle_line_ids = []
        products_order = self._product_order()
        for product_order in products_order:
            check = True
            if product_order['qty'] == 0:
                continue
            if len(therapy_bundle_line_ids) > 0:
                for therapy_bundle_line_id in therapy_bundle_line_ids:
                    if product_order['product_id'] == therapy_bundle_line_id[2]['product_id'] and product_order['qty'] == -1:
                        check = False
            if check:
                therapy_bundle_line_ids.append((0, 0, product_order))
            if product_order.get('body_area_ids', False):
                print(product_order['body_area_ids'])
                body_area_ids = product_order['body_area_ids']
                product_order['body_area_ids'] = []
                product_order['body_area_ids'].append((6, 0, body_area_ids))
                # print(product_order['body_area_ids'])
        therapy_bundle = {
            'order_id': self.id,
            'amount_total': self.amount_total,
            'therapy_record_id': self.x_therapy_record_id.id,
            'therapy_bundle_line_ids': therapy_bundle_line_ids,
        }
        self.env['therapy.bundle'].create(therapy_bundle)

    def _update_therapy_record_product(self, therapy_record):
        products_order = self._product_order(therapy_record.categ_id)
        for product_order in products_order:
            # check = True
            # if product_order['qty'] == 0:
            #     continue
            # if self.x_therapy_record_id.therapy_record_product_ids:
            #     for therapy_record_product in self.x_therapy_record_id.therapy_record_product_ids:
            #         if product_order['product_id'] == therapy_record_product.product_id.id:
            #             check = False
            #             if product_order['qty'] != -1:
            #                 therapy_record_product.qty_max = therapy_record_product.qty_max + product_order['qty']
            #             break
            # if check:
            self.env['therapy.record.product'].create({
                'therapy_record_id': therapy_record.id,
                'product_id': product_order['product_id'],
                'uom_id': product_order['uom_id'],
                'qty_used': 0,
                'qty_max': product_order['qty'],
                'body_area_ids': [(6, 0, product_order['body_area_ids'])],
                'order_id': product_order['order_id'],
                'order_line_id': product_order['order_line_id'],
                'price_unit': product_order['price_unit'],
                'price_subtotal_incl': product_order['price_subtotal_incl'],
            })

    @api.multi
    def action_order_confirm(self):
        Threapy_Obj = self.env['therapy.record']
        Category_Obj = self.env['product.category']
        ProductLot_Obj = self.env['stock.production.lot']
        super(PosOrder, self).action_order_confirm()
        if self.x_is_create_therapy_record:
            # self._create_therapy_bundle()  # Tạo gói liệu trình
            arr_category = []
            for order_line in self.lines:
                arr_category.append(order_line.x_categ_id.id)
            for category in Category_Obj.search([('id', 'in', arr_category)]):
                if category.x_is_therapy_record:
                    therapy_record = Threapy_Obj.search([('categ_id', '=', category.id), ('partner_id', '=', self.partner_id.id), ('state', 'not in', ['stop_care', 'cancel'])], limit=1)
                    if not therapy_record:
                        therapy_record = Threapy_Obj.create({
                            'name': f'{str(self.partner_id.name)} - {str(category.name)}',
                            'partner_id': self.partner_id.id,
                            'categ_id': category.id,
                        })
                    self._update_therapy_record_product(therapy_record)  # Đổ sản phẩm vào danh mục sản phẩm tồn trên hồ sơ trị liệu
        # thêm vùng cho thẻ dịch vụ (trong trường hợp bán buổi massage cho khách)
        product_lot_id = ProductLot_Obj.search([('x_order_id', '=', self.id)], limit=1)
        if product_lot_id:
            for order_line in self.lines:
                if (order_line.product_id.x_is_injection or order_line.product_id.x_is_massage) and len(
                        order_line.x_body_area_ids) > 0:
                    service_detail_id = self.env['izi.service.card.detail'].search(
                        [('lot_id', '=', product_lot_id.id), ('product_id', '=', order_line.product_id.id)])
                    service_detail_id.update({
                        'total_qty': service_detail_id.total_qty * len(order_line.x_body_area_ids),
                        'body_area_ids': [(6, 0, order_line.x_body_area_ids.ids)],
                    })
        else:
            raise UserError('Không tìm thấy thẻ dịch vụ của đơn hàng! Vui lòng kiểm tra lại để hoàn thành đơn hàng')

    # @api.multi
    # def confirm_refund(self):
    #     res = super(PosOrder, self).confirm_refund()
        # Refund gói liệu trình
        # therapy_bundle = self.env['therapy.bundle'].search([('order_id', '=', self.x_pos_partner_refund_id.id)])
        # if therapy_bundle:
        #     therapy_bundle.write({
        #         'state': 'cancel'
        #     })
        #     for order_line in self.lines:
        #         if not order_line.product_id.include_product_id and order_line.product_id.default_code != 'PDDV':
        #             raise UserError(
        #                 'Dịch vụ %s chưa được cấu hình sản phẩm đi kèm!' % (str(order_line.product_id.default_code)))
        #         if order_line.product_id.include_product_id:
        #             qty_include_product_id = abs(order_line.qty)
        #             include_product_id = order_line.product_id.include_product_id
        #
        #     therapy_bundle_line_injection = []
        #     for bundle_line in therapy_bundle.therapy_bundle_line_ids:
        #         if bundle_line.product_id.x_is_injection:
        #             therapy_bundle_line_injection.append(bundle_line.product_id.id)
        #
        #     therapy_record_products = self.env['therapy.record.product'].search(
        #         [('therapy_record_id', '=', therapy_bundle.therapy_record_id.id)])
        #     #Duyệt qua các sản phấm bán
        #     for therapy_record_product in therapy_record_products:
        #         for line in therapy_bundle.therapy_bundle_line_ids:
        #             if therapy_record_product.product_id == line.product_id:
        #                 if therapy_record_product.product_id != include_product_id: break
        #                 therapy_record_product.qty_max -= qty_include_product_id
        #         if therapy_record_product.qty_max == 0:
        #             therapy_record_product.unlink()
        #
        #     #Duyệt qua các sản phẩm bổ trợ
        #     for therapy_record_product in therapy_record_products:
        #         for line in self.x_pos_order_complement_ids:
        #             if therapy_record_product.product_id == line.product_id:
        #                 if therapy_record_product.product_id == include_product_id:
        #                     break
        #                 elif therapy_record_product.product_id.product_tmpl_id.x_is_injection:
        #                     therapy_record_product.qty_max = -1
        #                 else:
        #                     therapy_record_product.qty_max -= abs(line.qty)
        #         if therapy_record_product.qty_max == 0:
        #             therapy_record_product.unlink()
        # return res


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    x_body_area_ids = fields.Many2many('body.area', string='Body Area')
    x_is_massage = fields.Boolean(string='Is Massage', default=False, help="Pos order buy product which is massage")
    x_categ_id = fields.Many2one('product.category', related='product_id.categ_id', readonly=True, store=True)
    x_is_create_therapy = fields.Boolean(related='x_categ_id.x_is_therapy_record', string="Is create therapy record", store=True, readonly=True)
    x_use_compute_massage = fields.Boolean(string="Use amount compute massage")

    @api.depends('price_unit', 'tax_ids', 'qty', 'discount', 'product_id', 'x_discount', 'x_body_area_ids')
    def _compute_amount_line_all(self):
        for line in self:
            if line.product_id.x_is_massage or line.product_id.x_is_injection:
                line.x_is_massage = True
            if line.qty != 0:
                fpos = line.order_id.fiscal_position_id
                tax_ids_after_fiscal_position = fpos.map_tax(line.tax_ids, line.product_id,
                                                             line.order_id.partner_id) if fpos else line.tax_ids
                price = (line.price_unit - line.price_unit * line.discount / 100) - (line.x_discount / line.qty)
                # nếu bán dịch vụ massage theo thẻ dịch vụ thì nhân thêm số lg vùng vào tổng tiền
                if line.x_body_area_ids and line.product_id.x_is_massage:
                    price *= len(line.x_body_area_ids)
                taxes = tax_ids_after_fiscal_position.compute_all(price, line.order_id.pricelist_id.currency_id,
                                                                  line.qty,
                                                                  product=line.product_id,
                                                                  partner=line.order_id.partner_id)
                line.price_subtotal = line.price_subtotal_incl = taxes['total_included']

class PosOrderComplement(models.Model):
    _name = 'pos.order.complement'

    name = fields.Char(string='Pos Order Complement')
    product_id = fields.Many2one('product.product', string='Product')
    product_is_massage = fields.Boolean(related='product_id.x_is_massage', string='Product Is massage', readonly=True)
    product_is_injection = fields.Boolean(related='product_id.x_is_injection', string='Product Is Injection', readonly=True)
    product_is_medicine_day = fields.Boolean(related='product_id.x_is_medicine_day', string='Product Is Medicine Day', readonly=True)
    uom_id = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of  Measure', readonly=True)
    qty = fields.Integer(string='Qty')
    qty_max = fields.Integer(string='Qty max')
    note = fields.Char(string='Note')
    pos_order_id = fields.Many2one('pos.order', string='Pos Order')
    component_id = fields.Many2one('therapy.bundle.barem.component', string='Component')
    barem_id = fields.Many2one('therapy.bundle.barem', string="Barem")
    categ_id = fields.Many2one('product.category', related='barem_id.categ_id', readonly=True, store=True)


class PosOrderComputeMassage(models.TransientModel):
    _name = 'pos.order.compute.massage'
    _description = 'Compute massage'


    order_id = fields.Many2one('pos.order', string='Pos Order')
    body_area_number = fields.Integer(string="Body area number")
    amount_total = fields.Float(string="Amount total")
    massage_number = fields.Integer(string="Massage number", compute='_compute_massage_number')

    @api.depends('body_area_number', 'amount_total')
    def _compute_massage_number(self):
        for s in self:
            if s.body_area_number and s.amount_total:
                s.massage_number = int((s.amount_total * 1.2)/(1600000 * s.body_area_number))
            else:
                s.massage_number = 0

    @api.multi
    def action_confirm(self):
        if not self.order_id: raise UserError("Không có thông tin đơn hàng, không thể số buổi giảm béo cho đơn hàng.")

        for order_complement in self.order_id.x_pos_order_complement_ids:
            for barem_component in order_complement.barem_id.therapy_bundle_barem_component_ids:
                if order_complement.component_id.id == barem_component.id and barem_component.qty == -1:
                    if order_complement.product_is_massage:
                        order_complement.qty = self.massage_number
                        order_complement.qty_max = self.massage_number
                    elif order_complement.product_is_medicine_day:
                        pass
                    else:
                        order_complement.qty = int(self.massage_number/3.5)
                        order_complement.qty_max = int(self.massage_number/3.5)