# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from odoo.exceptions import except_orm, ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import math
import copy


class PosUserMaterialTmp(models.Model):
    _name = 'tmp.service.card.using'

    user_service_card_id = fields.Many2one('izi.service.card.using', string="Service Card Using")
    lines = fields.One2many('tmp.service.card.using.line', 'tmp_service_card_using', string="Detail Using Material")

    def _get_material_user(self,quantity, bom_id,use_material_id, using_stock_move):
        for line in bom_id.bom_line_ids:
            using_stock_move_obj = self.env['izi.using.stock.move.line'].search(
                [('use_material_id', '=', use_material_id.id), ('material_id', '=',line.product_id.id)])
            if using_stock_move_obj:
                using_stock_move_obj.quantity += line.product_qty * quantity/line.product_qty
            else:
                if line.product_id.uom_id.id != line.product_uom_id.id:
                    raise except_orm("Cảnh báo!", (
                        "Cấu hình đơn vị của nguyên vật liệu xuất khác với đơn vị tồn kho. Vui lòng kiểm tra lại"))
                argvs = {
                    'material_id': line.product_id.id,
                    'quantity': line.product_qty * quantity/bom_id.product_qty,
                    'uom_id': line.product_uom_id.id,
                    'use_material_id': use_material_id.id,
                    'use': True
                }
                using_stock_move.create(argvs)

    def _create_use_material(self, line):
        use_material_obj = self.env['pos.user.material']
        employee_ids = []
        for i in line.user_service_card_line_id.employee_ids:
            employee_ids.append(i.id)
        for j in line.user_service_card_line_id.doctor_ids:
            employee_ids.append(j.id)
        type_service = ''
        picking_type_id = self.user_service_card_id.pos_session_id.config_id.x_material_picking_type_id.id
        args = {
            'employee_ids': [(4, x) for x in employee_ids],
            'using_service_id': self.user_service_card_id.id,
            'date': self.user_service_card_id.redeem_date,
            'origin': self.user_service_card_id.name,
            'customer_id': self.user_service_card_id.customer_id.id,
            # 'service_ids': [(4, x.id) for x in line.service_id],
            # 'quantity': line.quantity,
            'picking_type_id': picking_type_id,
            'state':'draft',
        }
        user_material = use_material_obj.create(args)
        return user_material

    @api.multi
    def confirm(self):
        # Thẻ dịch vụ
        if self.user_service_card_id.type == 'card' and self.user_service_card_id.state != 'wait_approve':
            self.user_service_card_id.state = 'wait_material'
            using_stock_move = self.env['izi.using.stock.move.line']
            use_material_obj = self.env['pos.user.material']
            picking_type_id = self.user_service_card_id.pos_session_id.config_id.x_material_picking_type_id.id
            # count_service_pttm = 0
            use_bom = False #Có sử dụng định mức nvl
            for line in self.user_service_card_id.service_card_ids:
                if line.service_id.bom_service_count > 0: use_bom = True
                # Trừ dịch vụ trong thẻ
                service_card_detail_obj = self.env['izi.service.card.detail'].search(
                    [('lot_id', '=', line.serial_id.id), ('product_id', '=', line.service_id.id)])
                service_card_detail_obj.qty_use += line.quantity
                if service_card_detail_obj.remain_amount >= (
                        service_card_detail_obj.price_unit * line.quantity):
                    service_card_detail_obj.remain_amount -= service_card_detail_obj.price_unit * line.quantity
                else:
                    service_card_detail_obj.remain_amount = 0
            if use_bom:
                count_quantity = 0
                employees_ids = []
                service_ids = []
                args = {
                    'using_service_id': self.user_service_card_id.id,
                    'date': self.user_service_card_id.redeem_date,
                    'origin': self.user_service_card_id.name,
                    'customer_id': self.user_service_card_id.customer_id.id,
                    'picking_type_id': picking_type_id,
                }
                use_material_id = use_material_obj.create(args)
                # Tạo YCNL PTTM từ các dịch vụ trên Pupop
                for line in self.lines:
                    count_quantity += line.qty_using
                    for x in line.user_service_card_line_id.employee_ids:
                        employees_ids.append(x.id)
                    for y in line.user_service_card_line_id.doctor_ids:
                        employees_ids.append(y.id)
                    service_ids.append(line.product_id.id)
                    for tmp in line.bom_id.bom_line_ids:
                        using_stock_move_obj = self.env['izi.using.stock.move.line'].search(
                            [('use_material_id', '=', use_material_id.id),
                             ('material_id', '=', tmp.product_id.id)])
                        if using_stock_move_obj:
                            using_stock_move_obj.quantity += tmp.product_qty * line.qty_using
                        else:
                            if tmp.product_id.product_tmpl_id.uom_id.id != tmp.product_uom_id.id:
                                raise except_orm("Cảnh báo!", (
                                    "Cấu hình đơn vị của nguyên vật liệu xuất khác với đơn vị tồn kho. Vui lòng kiểm tra lại"))
                            argvs = {
                                'material_id': tmp.product_id.id,
                                'quantity': tmp.product_qty * line.qty_using,
                                'uom_id': tmp.product_uom_id.id,
                                'use_material_id': use_material_id.id,
                                'use': True
                            }
                            using_stock_move.create(argvs)
                use_material_id.update({'employee_ids': [(4, x) for x in employees_ids],
                                                'service_ids': [(4, x) for x in service_ids],
                                                'quantity': count_quantity})
            else:
                self.state = 'working'
                self.date_start = datetime.now()

        elif self.user_service_card_id.type in ['service', 'guarantee'] and self.user_service_card_id.state != 'wait_approve':
            self.user_service_card_id.state = 'wait_material'
            using_stock_move = self.env['izi.using.stock.move.line']
            use_material_obj = self.env['pos.user.material']
            picking_type_id = self.user_service_card_id.pos_session_id.config_id.x_material_picking_type_id.id
            # count_service_pttm = 0
            use_bom = False #Có sử dụng định mức nvl
            for line in self.user_service_card_id.service_card1_ids:
                if line.service_id.bom_service_count > 0: use_bom = True
            if use_bom:
                count_quantity = 0
                employees_ids = []
                service_ids = []
                args = {
                    'using_service_id': self.user_service_card_id.id,
                    'date': self.user_service_card_id.redeem_date,
                    'origin': self.user_service_card_id.name,
                    'customer_id': self.user_service_card_id.customer_id.id,
                    'picking_type_id': picking_type_id,
                }
                use_material_id = use_material_obj.create(args)
                # Tạo YCNL PTTM từ các dịch vụ trên Pupop
                for line in self.lines:
                    count_quantity += line.qty_using
                    for x in line.user_service_card_line_id.employee_ids:
                        employees_ids.append(x.id)
                    for y in line.user_service_card_line_id.doctor_ids:
                        employees_ids.append(y.id)
                    service_ids.append(line.product_id.id)
                    for tmp in line.bom_id.bom_line_ids:
                        using_stock_move_obj = self.env['izi.using.stock.move.line'].search(
                            [('use_material_id', '=', use_material_id.id),
                             ('material_id', '=', tmp.product_id.id)])
                        if using_stock_move_obj:
                            using_stock_move_obj.quantity += tmp.product_qty * line.qty_using
                        else:
                            if tmp.product_id.product_tmpl_id.uom_id.id != tmp.product_uom_id.id:
                                raise except_orm("Cảnh báo!", (
                                    "Cấu hình đơn vị của nguyên vật liệu xuất khác với đơn vị tồn kho. Vui lòng kiểm tra lại"))
                            argvs = {
                                'material_id': tmp.product_id.id,
                                'quantity': tmp.product_qty * line.qty_using,
                                'uom_id': tmp.product_uom_id.id,
                                'use_material_id': use_material_id.id,
                                'use': True
                            }
                            using_stock_move.create(argvs)
                use_material_id.update({'employee_ids': [(4, x) for x in employees_ids],
                                                'service_ids': [(4, x) for x in service_ids],
                                                'quantity': count_quantity})
            else:
                self.state = 'working'
                self.date_start = datetime.now()

            if self.user_service_card_id.type == 'service':
                # Tạo pos_order cho đơn h
                if not self.user_service_card_id.pos_order_id:
                    pos_order_obj = self.env['pos.order']
                    argvs = {
                        'session_id': self.user_service_card_id.pos_session_id.id,
                        'partner_id': self.user_service_card_id.customer_id.id,
                        'x_rank_id': self.user_service_card_id.rank_id.id,
                        'user_id': self.user_service_card_id.user_id.id,
                        'pricelist_id': self.user_service_card_id.pricelist_id.id,
                        'date_order': self.user_service_card_id.redeem_date,
                        'x_type': '3'
                    }
                    pos_order_id = pos_order_obj.create(argvs)
                    self.user_service_card_id.pos_order_id = pos_order_id.id
                    pos_order_line_obj = self.env['pos.order.line']
                    for line in self.user_service_card_id.service_card1_ids:
                        argvs = {
                            'product_id': line.service_id.id,
                            'qty': line.quantity,
                            'price_unit': line.price_unit,
                            'discount': line.discount,
                            'price_subtotal': line.amount,
                            'price_subtotal_incl': line.amount,
                            'order_id': pos_order_id.id,
                            'x_is_gift': False,
                        }
                        pos_order_line_obj.create(argvs)
                    # if self.pos_order_id.x_debt != 0:
                    #     self.pos_order_id.create_invoice()
                count = 0
                count1 = 0
                for line in self.user_service_card_id.service_card1_ids:
                    count += line.amount
                for line in self.user_service_card_id.pos_payment_service_ids:
                    count1 += line.amount
                if count != count1:
                    raise except_orm('Cảnh báo!',
                                     ('Bạn không thể hoàn thành khi số tiền thanh toán không bằng số tiền làm dịch vụ'))
                for line in self.user_service_card_id.pos_payment_service_ids:
                    x_lot_id = None
                    if line.x_vc_code:
                        x_lot_id = self.env['stock.production.lot'].search(
                            [('name', '=', line.x_vc_code.upper().strip())], limit=1).id
                    statement_id = False
                    for statement in self.user_service_card_id.pos_session_id.statement_ids:
                        if statement.id == statement_id:
                            journal_id = statement.journal_id.id
                            break
                        elif statement.journal_id.id == line.journal_id.id:
                            statement_id = statement.id
                            break
                    if not statement_id:
                        raise UserError(_('You have to open at least one cashbox.'))
                    company_cxt = dict(self.env.context, force_company=line.journal_id.company_id.id)
                    account_def = self.env['ir.property'].with_context(company_cxt).get(
                        'property_account_receivable_id',
                        'res.partner')
                    account_id = (self.user_service_card_id.customer_id.property_account_receivable_id.id) or (
                            account_def and account_def.id) or False
                    argvs = {
                        'ref': self.user_service_card_id.pos_session_id.name,
                        'name': pos_order_id.name,
                        'partner_id': self.user_service_card_id.customer_id.id,
                        'amount': line.amount,
                        'account_id': account_id,
                        'statement_id': statement_id,
                        'pos_statement_id': pos_order_id.id,
                        'journal_id': line.journal_id.id,
                        'date': self.user_service_card_id.redeem_date,
                        'x_vc_id': x_lot_id
                    }
                    pos_make_payment_id = self.env['account.bank.statement.line'].create(argvs)
                # pos_order_id.action_order_complete()
                if self.user_service_card_id.x_user_id:
                    self.user_service_card_id.pos_order_id.x_user_id = self.user_service_card_id.x_user_id
                pos_order_id.process_customer_signature()
                pos_order_id.action_order_confirm()
                self.user_service_card_id.pos_order_id.statement_ids.write({'x_ignore_reconcile': True})
        else:
            raise UserError("Loại đơn sddv %s và trạng thái đơn sddv %s" % (str(self.user_service_card_id.type), str(self.user_service_card_id.state)))

class PosUserMaterialLineTmp(models.Model):
    _name = 'tmp.service.card.using.line'

    tmp_service_card_using = fields.Many2one('tmp.service.card.using', string = 'Tmp user card ')
    bom_id = fields.Many2one('service.bom','Bom',)
    product_id = fields.Many2one('product.product','Product')
    qty_using = fields.Float('Qty Using')
    user_service_card_line_id = fields.Many2one('izi.service.card.using.line', "Using Line")




