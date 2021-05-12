from odoo import models, fields, api, _
from odoo.exceptions import except_orm


class PosPaymentAllocation(models.Model):
    _inherit = 'pos.payment.allocation'

    def auto_payment_allocation(self):
        if self.state != 'draft':
            raise except_orm('Cảnh báo', ("Trạng thái đơn hàng đã thay đổi. Vui lòng F5 hoặc tải lại trang"))
        self.state = 'done'
        if self.amount_remain != 0 or self.amount_allocation == 0:
            raise except_orm("Cảnh báo!", ("Bạn phải phân bổ hết số tiền trên đơn hàng"))
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