# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError, MissingError, except_orm


class IziServiceCardUsing(models.Model):
    _inherit = 'izi.service.card.using'

    type = fields.Selection([('service', "Service"), ('card', "Card"), ('guarantee', "Guarantee"), ('bundle', "Bundle"), ('guarantee_bundle', "Guarantee bundle")], default='card', required=1)
    therapy_prescription_id = fields.Many2one('therapy.prescription', string='Therapy Prescription')
    therapy_record_id = fields.Many2one('therapy.record', related='therapy_prescription_id.therapy_record_id', string='Therapy Record', store=True, readonly=True)
    service_bundle_ids = fields.One2many('izi.service.card.using.line', 'using_id', "Service Bundle", domain=lambda self: [('type', '=', 'service_bundle')], copy=False)
    is_body_area = fields.Boolean(string='Have body area', default=False)

    # @api.onchange('therapy_prescription_id')
    def _onchange_customer(self):
        if self.therapy_prescription_id:
            self.customer_id = self.therapy_prescription_id.partner_id.id

    def do_create_pos_work_service_allocation(self, service_card_using_ids):
        service_card_usings = self.env['izi.service.card.using'].search([('id', 'in', service_card_using_ids)])
        for service_card in service_card_usings:
            if service_card.type == 'card':
                for line in service_card.service_card_ids:
                    count_nv = 0
                    count_bs = 0
                    employee = ''
                    for x in line.employee_ids:
                        employee = employee + ', ' + str(x.name)
                        count_nv += 1
                    for y in line.doctor_ids:
                        employee = employee + ', ' + str(y.name)
                        count_bs += 1
                    pos_work_service_id = self.env['pos.work.service.allocation'].create({
                        'date': service_card.redeem_date,
                        'use_service_id': service_card.id,
                        'pos_session_id': service_card.pos_session_id.id,
                        'partner_id': service_card.customer_id.id,
                        'service_id': line.service_id.id,
                        'employee': employee,
                        'state': 'done',
                    })
                    for i in line.employee_ids:
                        self.env['pos.work.service.allocation.line'].create({
                            'pos_session_id': service_card.pos_session_id.id,
                            'service_id': line.service_id.id,
                            'partner_id': service_card.customer_id.id,
                            'employee_id': i.id,
                            'work_lt': line.quantity * (1 / count_nv) if count_nv > 0 else 0,
                            'work_change': line.quantity * (1 / count_nv) if count_nv > 0 else 0,
                            'date': service_card.redeem_date,
                            'work_nv': 'employee',
                            'pos_work_service_id': pos_work_service_id.id,
                            'use_service_id': service_card.id,
                            'use_service_line_id': line.id,
                        })
                    for i in line.doctor_ids:
                        self.env['pos.work.service.allocation.line'].create({
                            'pos_session_id': service_card.pos_session_id.id,
                            'service_id': line.service_id.id,
                            'partner_id': service_card.customer_id.id,
                            'employee_id': i.id,
                            'work_lt': line.quantity * (1 / count_bs) if count_bs > 0 else 0,
                            'work_change': line.quantity * (1 / count_bs) if count_bs > 0 else 0,
                            'date': service_card.redeem_date,
                            'work_nv': 'doctor',
                            'pos_work_service_id': pos_work_service_id.id,
                            'use_service_id': service_card.id,
                            'use_service_line_id': line.id,
                        })
            elif service_card.type == 'service':
                for line in service_card.service_card1_ids:
                    count_nv = 0
                    count_bs = 0
                    employee = ''
                    for x in line.employee_ids:
                        employee = employee  + ', ' + str(x.name)
                        count_nv += 1
                    for y in line.doctor_ids:
                        employee = employee + ', ' + str(y.name)
                        count_bs += 1
                    pos_work_service_id = self.env['pos.work.service.allocation'].create({
                        'date': service_card.redeem_date,
                        'use_service_id' : service_card.id,
                        'pos_session_id': service_card.pos_session_id.id,
                        'partner_id': service_card.customer_id.id,
                        'service_id' : line.service_id.id,
                        'employee': employee,
                        'state': 'done',
                    })
                    for i in line.employee_ids:
                        pos_work_service_line_id = self.env['pos.work.service.allocation.line'].create({
                            'pos_session_id': service_card.pos_session_id.id,
                            'service_id': line.service_id.id,
                            'partner_id': service_card.customer_id.id,
                            'employee_id': i.id,
                            'work_lt' : line.quantity *(1/count_nv) if count_nv >0 else 0,
                            'work_change': line.quantity *(1/count_nv) if count_nv >0 else 0,
                            'date': service_card.redeem_date,
                            'work_nv': 'employee',
                            'pos_work_service_id': pos_work_service_id.id,
                            'use_service_id': service_card.id,
                            'use_service_line_id': line.id,
                        })
                    for i in line.doctor_ids:
                        pos_work_service_line_id = self.env['pos.work.service.allocation.line'].create({
                            'pos_session_id': service_card.pos_session_id.id,
                            'service_id': line.service_id.id,
                            'partner_id': service_card.customer_id.id,
                            'employee_id': i.id,
                            'work_lt' : line.quantity *(1/count_bs) if count_bs >0 else 0,
                            'work_change': line.quantity *(1/count_bs) if count_bs >0 else 0,
                            'date': service_card.redeem_date,
                            'work_nv': 'doctor',
                            'pos_work_service_id': pos_work_service_id.id,
                            'use_service_id': service_card.id,
                            'use_service_line_id': line.id,
                        })
            else:
                for bundle in service_card.service_bundle_ids:
                    count_nv = 0
                    count_bs = 0
                    employee = ''
                    for x in bundle.employee_ids:
                        employee = employee + ', ' + str(x.name)
                        count_nv += 1
                    for y in bundle.doctor_ids:
                        employee = employee + ', ' + str(y.name)
                        count_bs += 1
                    pos_work_service_id = self.env['pos.work.service.allocation'].search([('use_service_id', '=', service_card.id), ('service_id', '=', bundle.service_id.id), ('employee', '=', employee)])
                    if not pos_work_service_id:
                        pos_work_service_id = self.env['pos.work.service.allocation'].create({
                            'date': service_card.redeem_date,
                            'use_service_id': service_card.id,
                            'pos_session_id': service_card.pos_session_id.id,
                            'partner_id': service_card.customer_id.id,
                            'service_id': bundle.service_id.id,
                            'employee': employee,
                            'state': 'done',
                        })
                    for i in bundle.employee_ids:
                        self.env['pos.work.service.allocation.line'].create({
                            'pos_session_id': service_card.pos_session_id.id,
                            'service_id': bundle.service_id.id,
                            'partner_id': service_card.customer_id.id,
                            'body_area_ids': [(6, 0, bundle.body_area_ids.ids)],
                            'employee_id': i.id,
                            'work_lt': bundle.quantity * (1 / count_nv) if count_nv > 0 else 0,
                            'work_change': bundle.quantity * (1 / count_nv) if count_nv > 0 else 0,
                            'date': service_card.redeem_date,
                            'work_nv': 'employee',
                            'pos_work_service_id': pos_work_service_id.id,
                            'use_service_id': service_card.id,
                            'use_service_line_id': bundle.id,
                        })
                    for i in bundle.doctor_ids:
                        self.env['pos.work.service.allocation.line'].create({
                            'pos_session_id': service_card.pos_session_id.id,
                            'service_id': bundle.service_id.id,
                            'partner_id': service_card.customer_id.id,
                            'body_area_ids': [(6, 0, bundle.body_area_ids.ids)],
                            'employee_id': i.id,
                            'work_lt': bundle.quantity * (1 / count_bs) if count_bs > 0 else 0,
                            'work_change': bundle.quantity * (1 / count_bs) if count_bs > 0 else 0,
                            'date': service_card.redeem_date,
                            'work_nv': 'doctor',
                            'pos_work_service_id': pos_work_service_id.id,
                            'use_service_id': service_card.id,
                            'use_service_line_id': bundle.id,
                        })


    @api.multi
    def action_done(self):
        TherapyProduct_Obj = self.env['therapy.record.product']
        res = super(IziServiceCardUsing, self).action_done()
        for line in self.service_bundle_ids:
            if line.state == 'new':
                line.action_confirm_bed()
            if line.state == 'working':
                line.action_done()
            if line.state != 'done':
                raise except_orm("Cảnh báo!", ("Vui lòng cập nhật trạng thái giường trước khi đóng đơn sử dụng"))
        #todo xử lý cập nhật tồn cho hồ sơ trị liệu
        if self.therapy_prescription_id and self.type == 'bundle' and self.therapy_prescription_id.state_using == 'open':
            therapy_record_id = self.env['therapy.record'].search([('id', '=', self.therapy_record_id.id)])
            if not therapy_record_id:
                raise UserError('Không tìm thấy hồ hơ trị liệu có tên %s' % therapy_record_id.name)
            for therapy_record_product_id in therapy_record_id.therapy_record_product_ids:
                therapy_quantity_used = 0
                for service_bundle_id in self.service_bundle_ids.filtered(lambda bundle:bundle.service_id.id == therapy_record_product_id.product_id.id):
                    if service_bundle_id.x_order_id.id == therapy_record_product_id.order_id.id and service_bundle_id.x_order_line_id.id == therapy_record_product_id.order_line_id.id:
                        therapy_quantity_used += service_bundle_id.quantity
                if therapy_quantity_used == 0:
                    continue
                else:
                    #nếu đơn sddv có cả bắn và massage thì k trừ buổi massage
                    # if therapy_record_product_id.product_id.x_is_massage and len(self.service_bundle_ids.filtered(lambda line: line.service_id.x_is_injection)) != 0:
                    #     pass
                    # else:
                    if therapy_record_product_id.product_id.x_is_massage:
                        # tính toán số dòng buổi massage và số vùng
                        service_massage_ids = self.service_bundle_ids.filtered(lambda line: line.x_order_id.id == service_bundle_id.x_order_id.id and line.service_id == therapy_record_product_id.product_id)
                        len_massage = len(service_massage_ids)
                        arr_area = []
                        for service_massage_id in service_massage_ids:
                            arr_area.append(service_massage_id.body_area_ids[0])
                        len_area = len(set(arr_area))
                        if len_massage == 0 and len_area == 0:
                            quantity_massage = 0
                        else:
                            quantity_massage = (len_massage / len_area)
                        therapy_record_product_id.qty_used += quantity_massage
                    else:
                        therapy_record_product_id.qty_used += therapy_quantity_used
            self.therapy_prescription_id.state_using == 'close'
        self.state = 'done'

        if len(self.pos_work_service_lines) > 0:
            for line in self.pos_work_service_lines:
                if line.pos_work_service_id:
                    line.pos_work_service_id.unlink()
                line.unlink()
        arr_service = []
        for line in self.service_card_ids:
            arr_service.append({
                'employee_ids': line.employee_ids,
                'doctor_ids': line.doctor_ids,
                'service_id': line.service_id.id,
                'quantity': line.quantity,
                'id': line.id,
            })
        for line in self.service_card1_ids:
            arr_service.append({
                'employee_ids': line.employee_ids,
                'doctor_ids': line.doctor_ids,
                'service_id': line.service_id.id,
                'quantity': line.quantity,
                'id': line.id,
            })
        for line in self.service_bundle_ids:
            arr_service.append({
                'employee_ids': line.employee_ids,
                'doctor_ids': line.doctor_ids,
                'service_id': line.service_id.id,
                'quantity': line.quantity,
                'id': line.id,
            })
        for line in arr_service:
            count_nv = 0
            count_bs = 0
            employee = ''
            for x in line['employee_ids']:
                employee = employee + ', ' + str(x.name)
                count_nv += 1
            for y in line['doctor_ids']:
                employee = employee + ', ' + str(y.name)
                count_bs += 1
            pos_work_service_id = self.env['pos.work.service.allocation'].create({
                'date': self.redeem_date,
                'use_service_id': self.id,
                'pos_session_id': self.pos_session_id.id,
                'partner_id': self.customer_id.id,
                'service_id': line['service_id'],
                'employee': employee,
                'state': 'done',
            })
            for i in line['employee_ids']:
                self.env['pos.work.service.allocation.line'].create({
                    'pos_session_id': self.pos_session_id.id,
                    'service_id': line['service_id'],
                    'partner_id': self.customer_id.id,
                    'employee_id': i.id,
                    'work_lt': line['quantity'] * (1 / count_nv) if count_nv > 0 else 0,
                    'work_change': line['quantity'] * (1 / count_nv) if count_nv > 0 else 0,
                    'date': self.redeem_date,
                    'work_nv': 'employee',
                    'pos_work_service_id': pos_work_service_id.id,
                    'use_service_id': self.id,
                    'use_service_line_id': line['id'],
                })
            for i in line['doctor_ids']:
                self.env['pos.work.service.allocation.line'].create({
                    'pos_session_id': self.pos_session_id.id,
                    'service_id': line['service_id'],
                    'partner_id': self.customer_id.id,
                    'employee_id': i.id,
                    'work_lt': line['quantity'] * (1 / count_bs) if count_bs > 0 else 0,
                    'work_change': line['quantity'] * (1 / count_bs) if count_bs > 0 else 0,
                    'date': self.redeem_date,
                    'work_nv': 'doctor',
                    'pos_work_service_id': pos_work_service_id.id,
                    'use_service_id': self.id,
                    'use_service_line_id': line['id'],
                })

    def _check_required_service(self):
        # param_obj = self.env['ir.config_parameter']
        # code = param_obj.get_param('default_code_product_category_material')
        # if not code:
        #     raise ValidationError(
        #         _(
        #             u"Bạn chưa cấu hình thông số hệ thống cho mã nhóm xuất NVL là default_code_product_category_material. Xin hãy liên hệ với người quản trị."))
        # list = code.split(',')
        if self.state != 'draft':
            raise except_orm('Cảnh báo!',
                             ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc tải lại trang"))
        else:
            if self.state != 'draft':
                raise except_orm('Cảnh báo!',
                                 ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc tải lại trang"))
        for line in self.service_bundle_ids:
            if line.quantity == 0:
                line.unlink()
            else:
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
            raise except_orm("Thông báo", "Không có phiên POS nào đang mở. Xin hãy mở phiên trước khi thao tác !!")
        else:
            self.pos_session_id = my_session.id

    @api.multi
    def action_apply_change_employee(self):
        pos_work_service_allocation_obj = self.env['pos.work.service.allocation'].search(
            [('use_service_id', '=', self.id)])
        for line in pos_work_service_allocation_obj:
            line.unlink()
        pos_work_service_allocation_line_obj = self.env['pos.work.service.allocation.line'].search(
            [('use_service_id', '=', self.id)])
        for i in pos_work_service_allocation_line_obj:
            i.unlink()
        arr_service = []
        for line in self.service_card_ids:
            arr_service.append({
                'employee_ids': line.employee_ids,
                'doctor_ids': line.doctor_ids,
                'service_id': line.service_id.id,
                'quantity': line.quantity,
                'id': line.id,
            })
        for line in self.service_card1_ids:
            arr_service.append({
                'employee_ids': line.employee_ids,
                'doctor_ids': line.doctor_ids,
                'service_id': line.service_id.id,
                'quantity': line.quantity,
                'id': line.id,
            })
        for line in self.service_bundle_ids:
            arr_service.append({
                'employee_ids': line.employee_ids,
                'doctor_ids': line.doctor_ids,
                'service_id': line.service_id.id,
                'quantity': line.quantity,
                'id': line.id,
            })
        for line in arr_service:
            count_nv = 0
            count_bs = 0
            employee = ''
            for x in line['employee_ids']:
                employee = employee + ', ' + str(x.name)
                count_nv += 1
            for y in line['doctor_ids']:
                employee = employee + ', ' + str(y.name)
                count_bs += 1
            pos_work_service_id = self.env['pos.work.service.allocation'].create({
                'date': self.redeem_date,
                'use_service_id': self.id,
                'pos_session_id': self.pos_session_id.id,
                'partner_id': self.customer_id.id,
                'service_id': line['service_id'],
                'employee': employee,
                'state': 'done',
            })
            for i in line['employee_ids']:
                pos_work_service_line_id = self.env['pos.work.service.allocation.line'].create({
                    'pos_session_id': self.pos_session_id.id,
                    'service_id': line['service_id'],
                    'partner_id': self.customer_id.id,
                    'employee_id': i.id,
                    'work_lt': line['quantity'] * (1 / count_nv) if count_nv > 0 else 0,
                    'work_change': line['quantity'] * (1 / count_nv) if count_nv > 0 else 0,
                    'date': self.redeem_date,
                    'work_nv': 'employee',
                    'pos_work_service_id': pos_work_service_id.id,
                    'use_service_id': self.id,
                    'use_service_line_id': line['id']
                })
            for i in line['doctor_ids']:
                pos_work_service_line_id = self.env['pos.work.service.allocation.line'].create({
                    'pos_session_id': self.pos_session_id.id,
                    'service_id': line['service_id'],
                    'partner_id': self.customer_id.id,
                    'employee_id': i.id,
                    'work_lt': line['quantity'] * (1 / count_bs) if count_bs > 0 else 0,
                    'work_change': line['quantity'] * (1 / count_bs) if count_bs > 0 else 0,
                    'date': self.redeem_date,
                    'work_nv': 'doctor',
                    'pos_work_service_id': pos_work_service_id.id,
                    'use_service_id': self.id,
                    'use_service_line_id': line['id']
                })
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_print_work(self):
        if self.service_card_ids or self.service_card1_ids:
            print('a')
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/izi_therapy_record.report_template_work_service_view/%s' % (str(self.id)),
            'target': 'new',
            'res_id': self.id,
        }

    @api.multi
    def action_confirm_bundle(self):
        if self.type == 'bundle':
            # kiểm tra dịch vụ có sử dụng bác sĩ?
            for service_card in self.service_bundle_ids:
                if service_card.service_id.x_use_doctor and not service_card.doctor_ids and service_card.quantity != 0:
                    raise ValidationError('Dịch vụ [%s]%s phải chọn bác sĩ!' % (str(service_card.service_id.default_code), str(service_card.service_id.name)))

            #kiểm tra đã chọn bác sĩ, khách hàng, tư vấn viên,.. hay chưa? kiểm tra phiên bán hàng
            self._check_required_service()
            #kiểm tra số lượng sử dụng trong đơn sddv
            count = 0
            for line in self.service_bundle_ids:
                if line.quantity != 0:
                    count += 1
            if count == 0:
                raise except_orm('Cảnh báo!',
                                 ("Số lượng dịch vụ không thể bằng không.Vui lòng xóa hoặc thay đổi số lượng!"))
            choose_bom = False #Kiểm tra đơn sddv có dịch vụ được cấu hình nhiều định mức nvl
            use_bom = False #Kiểm tra đơn sddv có dịch vụ được cấu hình định mức nvl
            picking_type_id = self.pos_session_id.config_id.x_material_picking_type_id.id
            for line in self.service_bundle_ids:
                if line.service_id.bom_service_count >= 1:
                    use_bom = True
                    self._get_material_user(line.quantity, line.service_id, self.id, line)
                    if line.service_id.bom_service_count > 1:
                        choose_bom = True
            if not use_bom:
                self.state = 'working'
                self.date_start = datetime.now()
            elif choose_bom:
                tmp_service_obj = self.env['tmp.service.card.using'].search(
                    [('user_service_card_id', '=', self.id)])
                view = self.env.ref('izi_use_service_card.tmp_pos_use_material_view')
                return {
                    'name': _('Choose?'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'tmp.service.card.using',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': tmp_service_obj.id,
                    'context': self.env.context,
                }
            else:
                self.state = 'wait_material'
                using_stock_move = self.env['izi.using.stock.move.line']
                use_material_obj = self.env['pos.user.material']

                # Kiểm tra xem dịch vụ được xuất từ kho nào
                # count_service_pttm, count_service, picking_type_pttm_id, picking_type_id = self._check_service_exported_stock()
                # xử lý tạo đơn xuất nguyên vật liệu
                # korea ycau tách đơn yêu cầu nvl theo từng dịch vụ
                for line in self.service_bundle_ids.filtered(lambda line: line.service_id.bom_service_count >= 1):
                    employees_ids = []
                    args = {
                        'using_service_id': self.id,
                        'date': self.redeem_date,
                        'origin': self.name,
                        'customer_id': self.customer_id.id,
                        'picking_type_id': picking_type_id,
                        'service_ids': [(4, line.service_id.id)],
                        'quantity': line.quantity,
                    }
                    use_material_id = use_material_obj.create(args)
                # for line in self.service_bundle_ids:
                    if line.service_id.bom_service_count > 0:
                        for x in line.employee_ids:
                            employees_ids.append(x.id)
                        for y in line.doctor_ids:
                            employees_ids.append(y.id)
                        service_bom_obj = self.env['service.bom'].search(
                            [('product_tmpl_id', '=', line.service_id.product_tmpl_id.id),
                             ('product_id', '=', line.service_id.id)])
                        if len(service_bom_obj) > 1:
                            raise except_orm("Thông báo", (
                                "Đang có nhiều định mức cho dịch vụ này. Vui lòng liên hệ Admintrantor để kiểm tra"))
                        for tmp in service_bom_obj.bom_line_ids:
                            using_stock_move_obj = self.env['izi.using.stock.move.line'].search(
                                [('use_material_id', '=', use_material_id.id),
                                 ('material_id', '=', tmp.product_id.id)])
                            if using_stock_move_obj:
                                using_stock_move_obj.quantity += tmp.product_qty * line.quantity
                            else:
                                if tmp.product_id.product_tmpl_id.uom_id.id != tmp.product_uom_id.id:
                                    raise except_orm("Cảnh báo!", (
                                        "Cấu hình đơn vị của nguyên vật liệu xuất khác với đơn vị tồn kho. Vui lòng kiểm tra lại"))
                                argvs = {
                                    'material_id': tmp.product_id.id,
                                    'quantity': tmp.product_qty * line.quantity,
                                    'uom_id': tmp.product_uom_id.id,
                                    'use_material_id': use_material_id.id,
                                    'use': True
                                }
                                using_stock_move.create(argvs)
                    use_material_id.update({'employee_ids': [(4, x) for x in employees_ids]})

                    if self.pos_session_id.config_id.x_auto_export_import_materials:
                        use_material_id.action_set_default_value()
                        use_material_id.force_available()
                        use_material_id.action_done()

    @api.multi
    def action_confirm_guarantee_bundle(self):
        picking_type_id = self.pos_session_id.config_id.x_material_picking_type_id.id
        if self.state != 'wait_payment':
            raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc tải lại trang"))
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
            raise except_orm("Thông báo", "Không có phiên POS nào đang mở. Xin hãy mở phiên trước khi thao tác !!")
        else:
            self.pos_session_id = my_session.id
        if not self.type == 'guarantee_bundle': raise UserError("Đơn sử dụng dịch vụ %s không thể xác nhận bảo hành gói liệu trình!" % (str(self.type)))
        count = 0
        for line in self.service_card1_ids:
            if line.quantity != 0:
                count += 1
                if (len(line.employee_ids) + len(line.doctor_ids)) == 0:
                    raise except_orm('Cảnh báo!', ('Bạn cần chọn kỹ thuật viên trước khi xác nhận'))
        if count == 0:
            raise except_orm('Cảnh báo!',
                             ("Số lượng dịch vụ không thể bằng không.Vui lòng xóa hoặc thay đổi số lượng!"))
        for line in self.service_card1_ids:
            if line.quantity == 0:
                line.unlink()
        tmp_service_obj = self.env['tmp.service.card.using'].search([('user_service_card_id', '=', self.id)])
        for line in tmp_service_obj:
            for tmp in line.lines:
                tmp.unlink()
            line.unlink()
        use_bom = False
        choose_bom = False
        for line in self.service_card1_ids:
            if line.service_id.bom_service_count >= 1:
                use_bom = True
                self._get_material_user(line.quantity, line.service_id, self.id, line)
                if line.service_id.bom_service_count > 1:
                    choose_bom = True

        if not use_bom:
            self.state = 'working'
            self.date_start = datetime.now()
        elif choose_bom:
            tmp_service_obj = self.env['tmp.service.card.using'].search(
                [('user_service_card_id', '=', self.id)])
            view = self.env.ref('izi_use_service_card.tmp_pos_use_material_view')
            return {
                'name': _('Choose?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'tmp.service.card.using',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': tmp_service_obj.id,
                'context': self.env.context,
            }
        else:
            self.state = 'wait_material'
            using_stock_move = self.env['izi.using.stock.move.line']
            use_material_obj = self.env['pos.user.material']
            # xử lý tạo đơn xuất nguyên vật liệu
            # korea ycau tách đơn yêu cầu nvl theo từng dịch vụ
            for line in self.service_card1_ids.filtered(lambda line: line.service_id.bom_service_count >= 1):
                employees_ids = []
                args = {
                    'using_service_id': self.id,
                    'date': self.redeem_date,
                    'origin': self.name,
                    'customer_id': self.customer_id.id,
                    'picking_type_id': picking_type_id,
                    'service_ids': [(4, line.service_id.id)],
                    'quantity': line.quantity,
                }
                use_material_id = use_material_obj.create(args)
            # for line in self.service_card1_ids:
                if line.service_id.bom_service_count > 0:
                    for x in line.employee_ids:
                        employees_ids.append(x.id)
                    for y in line.doctor_ids:
                        employees_ids.append(y.id)
                    service_bom_obj = self.env['service.bom'].search(
                        [('product_tmpl_id', '=', line.service_id.product_tmpl_id.id),
                         ('product_id', '=', line.service_id.id)])
                    if len(service_bom_obj) > 1:
                        raise except_orm("Thông báo", (
                            "Đang có nhiều định mức cho dịch vụ này. Vui lòng liên hệ Administrator để kiểm tra"))
                    for tmp in service_bom_obj.bom_line_ids:
                        using_stock_move_obj = self.env['izi.using.stock.move.line'].search(
                            [('use_material_id', '=', use_material_id.id),
                             ('material_id', '=', tmp.product_id.id)])
                        if using_stock_move_obj:
                            using_stock_move_obj.quantity += tmp.product_qty * line.quantity
                        else:
                            if tmp.product_id.product_tmpl_id.uom_id.id != tmp.product_uom_id.id:
                                raise except_orm("Cảnh báo!", (
                                    "Cấu hình đơn vị của nguyên vật liệu xuất khác với đơn vị tồn kho. Vui lòng kiểm tra lại"))
                            argvs = {
                                'material_id': tmp.product_id.id,
                                'quantity': tmp.product_qty * line.quantity,
                                'uom_id': tmp.product_uom_id.id,
                                'use_material_id': use_material_id.id,
                                'use': True
                            }
                            using_stock_move.create(argvs)
                use_material_id.update({'employee_ids': [(4, x) for x in employees_ids]})

                if self.pos_session_id.config_id.x_auto_export_import_materials:
                    use_material_id.action_set_default_value()
                    use_material_id.force_available()
                    use_material_id.action_done()
        #Làm trò mèo! Do chưa tìm ra nguyên nhân state của line bị null nên code này sẽ cưỡng bức state = 'new'
        for line in self.service_card1_ids:
            line.state = 'new'
        pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search(
            [('partner_id', '=', self.customer_id.id), ('state', '=', 'draft'), ('session_id', '=',self.pos_session_id.id)])
        if pos_sum_digital_obj:
            self.x_digital_sign_id = pos_sum_digital_obj.id
        else:
            pos_sum_digital_obj = self.env['pos.sum.digital.sign'].create({
                'partner_id': self.customer_id.id,
                'state': 'draft',
                'date': date.today(),
                'session_id': self.pos_session_id.id,
            })
            self.x_digital_sign_id = pos_sum_digital_obj.id

        for line in self.service_card1_ids:
            line.update({'x_digital_sign_id': pos_sum_digital_obj.id})

    @api.multi
    def process_refund(self):
        if self.type in ['bundle', 'guarantee_bundle']:
            # cập nhật lại số lượng đã sử dụng của sp trong tồn hstl
            therapy_record_id = self.env['therapy.record'].search([('id', '=', self.therapy_record_id.id)])
            if self.state == 'done' and self.type == 'bundle':
                for therapy_record_product_id in therapy_record_id.therapy_record_product_ids:
                    therapy_quantity_used = 0
                    for service_bundle_id in self.service_bundle_ids.filtered(
                            lambda bundle: bundle.service_id.id == therapy_record_product_id.product_id.id):
                        if service_bundle_id.x_order_id.id == therapy_record_product_id.order_id.id and service_bundle_id.x_order_line_id.id == therapy_record_product_id.order_line_id.id:
                            therapy_quantity_used += service_bundle_id.quantity
                    if therapy_quantity_used == 0:
                        continue
                    else:
                        # nếu đơn sddv có cả bắn và massage thì k trừ buổi massage
                        # if therapy_record_product_id.product_id.x_is_massage and len(
                        #         self.service_bundle_ids.filtered(lambda line: line.service_id.x_is_injection)) != 0:
                        #     pass
                        # else:
                        if therapy_record_product_id.product_id.x_is_massage:
                            # tính toán số dòng buổi massage và số vùng
                            service_massage_ids = self.service_bundle_ids.filtered(lambda
                                                                                       line: line.x_order_id.id == service_bundle_id.x_order_id.id and line.service_id == therapy_record_product_id.product_id)
                            len_massage = len(service_massage_ids)
                            arr_area = []
                            for service_massage_id in service_massage_ids:
                                arr_area.append(service_massage_id.body_area_ids[0])
                            len_area = len(set(arr_area))
                            if len_massage == 0 and len_area == 0:
                                quantity_massage = 0
                            else:
                                quantity_massage = (len_massage / len_area)
                            therapy_record_product_id.qty_used -= quantity_massage
                        else:
                            therapy_record_product_id.qty_used -= therapy_quantity_used



            self.update({'state': 'wait_confirm'})
            self.action_confirm_refund()
            return {'type': 'ir.actions.act_window_close'}
        elif self.type == 'service':
            self.update({'state': 'wait_confirm'})
            self.action_confirm_refund()
            pos_order_refund = self.env['pos.order'].search([('x_pos_partner_refund_id', '=', self.pos_order_id.id)])
            # pos_order_refund.send_refund()
            # pos_order_refund.confirm_refund()
            view = self.env.ref('point_of_sale.view_pos_pos_form')
            return {
                'name': _('Customer Signature?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.order',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': '',
                'res_id': pos_order_refund.id,
                'context': self.env.context,
            }
        else:
            self.update({'state': 'wait_confirm'})
            return {'type': 'ir.actions.act_window_close'}
        department_rate_ids = self.env['department.rate'].search([('using_id', '=', self.id)])
        if department_rate_ids:
            for department_rate_id in department_rate_ids:
                for line_rate in department_rate_id.line_ids:
                    line_rate.unlink()
                department_rate_id.unlink()

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Cảnh báo!', ('Bạn không thể xóa khi khác trạng thái nháp'))
                if self.therapy_prescription_id:
                    raise except_orm('Cảnh báo!', ('Bạn không thể xóa khi đơn sử dụng dịch vụ này được sinh ra từ PCD. Vui lòng hủy PCĐ để hủy đơn sddv'))
        return super(IziServiceCardUsing, self).unlink()


class IziServiceCardUsingLine(models.Model):
    _inherit = 'izi.service.card.using.line'

    body_area_ids = fields.Many2many('body.area', string='Body Area')
    therapy_prescription_id = fields.Many2one('therapy.prescription', string='Therapy Prescription')
    therapy_record_id = fields.Many2one('therapy.record', related='therapy_prescription_id.therapy_record_id', string='Therapy Record', store=True, readonly=True)
    is_massage = fields.Boolean(string='Is Massage', related='service_id.x_is_massage', store=True, readonly=True)
    is_injection = fields.Boolean(string='Is Injection', related='service_id.x_is_injection', store=True, readonly=True)
    x_order_line_id = fields.Many2one('pos.order.line', string='Pos Order Line')
    x_order_id = fields.Many2one('pos.order', string='Pos Order')
    type = fields.Selection(
        [('service_card', 'service_card'), ('service_card1', 'service_card1'), ('service_bundle', 'service_bundle')], string='Type')