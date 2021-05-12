# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm

class PosPaymentAllocation(models.Model):
    _name = 'pos.payment.allocation'
    _order = "id desc"

    name = fields.Char("Name", default='/')
    order_id = fields.Many2one('pos.order', "Order")
    date = fields.Date("Date")
    partner_id = fields.Many2one('res.partner', "Partner")
    invoice_id = fields.Many2one('account.invoice', "Invoice")
    amount_total = fields.Float("Amount Total") #Tổng sso tiền
    amount_allocation = fields.Float("Amount Allocation") # Số tiền đã phân bổ
    amount_remain = fields.Float("Amount Remain") # Số tiền còn lại
    state = fields.Selection([('draft', "Draft"), ('done', "Done"), ('cancel', "Cancel")], default='draft')
    payment_allocation_ids = fields.One2many('pos.payment.allocation.line', 'payment_allocation_id', "Payment Allocation")
    default_unlink = fields.Boolean("Default Unlink", default=False)
    destroy_service_id = fields.Many2one('pos.destroy.service', "Destroy Service")

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft' or self.default_unlink == True:
                raise except_orm("Cảnh báo!", ("Bạn không thể xóa khi trạng thái khác tạo mới"))
        return super(PosPaymentAllocation, self).unlink()

    @api.onchange('payment_allocation_ids')
    def _onchange_lines(self):
        allocated = 0.0
        for line in self.payment_allocation_ids:
            allocated += line.amount
        self.amount_allocation = allocated
        self.amount_remain = self.amount_total - allocated

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pos.payment.allocation') or _('New')
        return super(PosPaymentAllocation, self).create(vals)

    @api.multi
    def action_pos_payment_allocation(self):
        if self.state != 'draft':
            raise except_orm('Cảnh báo', ("Trạng thái đơn hàng đã thay đổi. Vui lòng F5 hoặc tải lại trang"))
        self.state = 'done'
        if int(self.amount_remain) != 0 or int(self.amount_allocation) == 0:
            raise except_orm("Cảnh báo!", ("Bạn phải phân bổ hết số tiền trên đơn hàng"))
        if int(self.amount_total) != int(self.amount_allocation):
            raise except_orm("Cảnh báo!", ("Bạn phải phân bổ đúng số tiền đã thanh toán trên đơn hàng"))
        # Phân bổ vào đơn hàng chính và thẻ dịch vụ nếu có
        for line in self.order_id.lines:
            for i in self.payment_allocation_ids:
                if line.id == i.order_line_id.id:
                    line.x_amount_payment += i.amount
        lot_id = self.env['stock.production.lot']
        for line in self.order_id.lines:
            if line.product_id.product_tmpl_id.x_type_card == 'tdv':
                lot_id = self.env['stock.production.lot'].search([('name', '=', line.lot_name)])
        for tmp in lot_id.x_card_detail_ids:
            for x in self.payment_allocation_ids:
                if tmp.product_id.id == x.product_id.id:
                    tmp.amount_payment += x.amount
        # Đối với trường hợp hủy dịch vụ
        if self.order_id.x_type == '4':
            pos_destroy = self.env['pos.destroy.service'].search([('new_order_id', '=', self.order_id.id)])
            lot_id = pos_destroy.product_lot_id
            for tmp in lot_id.x_card_detail_ids:
                for x in self.payment_allocation_ids:
                    if tmp.product_id.id == x.product_id.id:
                        tmp.amount_payment += x.amount
        # Sangla thêm phân bổ thanh toán đối với sản phẩm có bán nợ trên đơn hàng (Cập nhật vào trong bản ghi ghi nợ sản phẩm)
        pos_debit = self.env['pos.debit.good'].search([('partner_id', '=', self.partner_id.id)])
        for line in self.order_id.lines:
            if line.product_id.product_tmpl_id.x_type_card == 'none' and line.product_id.product_tmpl_id.type == 'product':
                if not self.order_id.x_pos_partner_refund_id:
                    if line.qty != line.x_qty and line.qty > 0:
                        if pos_debit:
                            pos_debit_line = self.env['pos.debit.good.line'].search(
                                [('product_id', '=', line.product_id.id), ('order_id', '=', self.order_id.id),
                                 ('debit_id', '=', pos_debit.id)])
                            if len(pos_debit_line) != 1:
                                raise except_orm("Thông báo!", ("Liên hệ với Admintrantor để xem đơn nợ hàng"))
                            else:
                                for x in self.payment_allocation_ids:
                                    if line.product_id.id == x.product_id.id:
                                        pos_debit_line.amount_payment += x.amount
                else:
                    if pos_debit:
                        pos_debit_line = self.env['pos.debit.good.line'].search(
                            [('product_id', '=', line.product_id.id), ('order_id', '=', self.order_id.x_pos_partner_refund_id.id),
                             ('debit_id', '=', pos_debit.id)])
                        if len(pos_debit_line) > 1:
                            raise except_orm("Thông báo!", ("Liên hệ với Admintrantor để xem đơn nợ hàng"))
                        elif len(pos_debit_line) == 0:
                            continue
                        else:
                            for x in self.payment_allocation_ids:
                                if line.product_id.id == x.product_id.id:
                                    pos_debit_line.amount_payment += x.amount
        # hết
        # Nếu là đơn hàng refund thì cập nhật lại vào đơn hàng gốc.
        # Nếu là đơn hủy dịch vụ ==> Tìm đơn hàng gốc cập nhật lại
        if self.order_id.x_pos_partner_refund_id:
            for line in self.payment_allocation_ids:
                if line.amount == 0:
                    continue
                for x in self.order_id.x_pos_partner_refund_id.lines:
                    if x.price_subtotal_incl !=0 :
                        if line.product_id.id == x.product_id.id:
                            x.x_amount_payment += line.amount
        if self.order_id.x_type == '4':
            pos_destroy = self.env['pos.destroy.service'].search([('new_order_id', '=', self.order_id.id)])
            for line in self.payment_allocation_ids:
                if line.amount == 0:
                    continue
                for x in pos_destroy.pos_order_id.lines:
                    if x.price_subtotal_incl != 0:
                        if line.product_id.id == x.product_id.id:
                            x.x_amount_payment += line.amount


    @api.multi
    def action_back(self):
        if self.state != 'done':
            raise except_orm('Cảnh báo', ("Trạng thái đơn hàng đã thay đổi. Vui lòng F5 hoặc tải lại trang"))
        self.state = 'draft'
        for line in self.order_id.lines:
            for i in self.payment_allocation_ids:
                if line.id == i.order_line_id.id:
                    line.x_amount_payment -= i.amount
        lot_id = self.env['stock.production.lot']
        for line in self.order_id.lines:
            if line.product_id.product_tmpl_id.x_type_card == 'tdv':
                lot_id = self.env['stock.production.lot'].search([('name', '=', line.lot_name)])
        for tmp in lot_id.x_card_detail_ids:
            for x in self.payment_allocation_ids:
                if tmp.product_id.id == x.product_id.id:
                    tmp.amount_payment -= x.amount
        # Đối với trường hợp hủy dịch vụ
        if self.order_id.x_type == '4':
            pos_destroy = self.env['pos.destroy.service'].search([('new_order_id', '=', self.order_id.id)])
            lot_id = pos_destroy.product_lot_id
            for tmp in lot_id.x_card_detail_ids:
                for x in self.payment_allocation_ids:
                    if tmp.product_id.id == x.product_id.id:
                        tmp.amount_payment -= x.amount

        # Sangla thêm phân bổ thanh toán đối với sản phẩm
        pos_debit = self.env['pos.debit.good'].search([('partner_id', '=', self.partner_id.id)])
        for line in self.order_id.lines:
            if line.product_id.product_tmpl_id.x_type_card == 'none' and line.product_id.product_tmpl_id.type == 'product':
                if not self.order_id.x_pos_partner_refund_id:
                    if line.qty != line.x_qty and line.qty > 0:
                        if pos_debit:
                            pos_debit_line = self.env['pos.debit.good.line'].search(
                                [('product_id', '=', line.product_id.id), ('order_id', '=', self.order_id.id),
                                 ('debit_id', '=', pos_debit.id)])
                            if len(pos_debit_line) != 1:
                                raise except_orm("Thông báo!", ("Liên hệ với Admintrantor để xem đơn nợ hàng"))
                            else:
                                for x in self.payment_allocation_ids:
                                    if line.product_id.id == x.product_id.id:
                                        pos_debit_line.amount_payment -= x.amount
                else:
                    if pos_debit:
                        pos_debit_line = self.env['pos.debit.good.line'].search(
                            [('product_id', '=', line.product_id.id), ('order_id', '=', self.order_id.id),
                             ('debit_id', '=', pos_debit.id)])
                        if len(pos_debit_line) > 1:
                            raise except_orm("Thông báo!", ("Liên hệ với Admintrantor để xem đơn nợ hàng"))
                        elif len(pos_debit_line) == 0:
                            continue
                        else:
                            for x in self.payment_allocation_ids:
                                if line.product_id.id == x.product_id.id:
                                    pos_debit_line.amount_payment -= x.amount