# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError, MissingError, except_orm


class TherapyPrescriptionReturnProduct(models.Model):
    _name = 'therapy.prescription.return.product'
    _rec_name = 'therapy_prescription_id'
    _description = u'Therapy Prescription Return Product'


    therapy_prescription_id = fields.Many2one('therapy.prescription', string='Therapy Prescription')
    therapy_record_id = fields.Many2one('therapy.record', string='Therapy Record')
    date_return = fields.Date(string='Date return',default=fields.Date.today())
    user_id = fields.Many2one('res.users', string='User')
    state = fields.Selection([('new', 'New'), ('done', 'Done'), ('cancel', 'Cancel')], default='new')
    therapy_prescription_return_product_line_ids = fields.One2many('therapy.prescription.return.product.line',
                                                                   'therapy_prescription_return_product_id',
                                                                   string='Therapy Prescription Return Product Line')
    picking_id = fields.Many2one('stock.picking', string='Picking')

    @api.multi
    def action_confirm(self):
        for detail in self.therapy_prescription_id:
            if detail.state != 'confirm':
                raise except_orm('Cảnh báo!', ("Phiếu chỉ định đã chuyển trạng thái, vui lòng tải lại trang để cập nhật!"))
            detail.state = 'transfer_confirmation'
            query = """
                        SELECT id FROM therapy_prescription_return_product
                        WHERE therapy_prescription_id = %s
                        AND state = 'new'
                        """
            self._cr.execute(query, ([self.therapy_prescription_id.id]))
            res = self._cr.dictfetchall()
            if len(res) > 1:
                raise except_orm('Cảnh báo!', (
                            "Đang có %s đơn trả hàng ở trạng thái mới. Liên hệ Admin để được giải quyết hoặc tải lại trang.Xin cám ơn!" % len(res)))

    @api.multi
    def action_cancel(self):
        if self.picking_id.state != 'done':
            raise ValidationError('Đơn nhập kho chưa được hoàn thành.Vui lòng kiểm tra lại')
        self.picking_id.state = 'cancel'
        self.state = 'cancel'

class TherapyPrescriptionReturnProductLine(models.Model):
    _name = 'therapy.prescription.return.product.line'

    product_id = fields.Many2one('product.product', string='Product')
    qty = fields.Float(string='Quantity')
    uom_id = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure', readonly=1)
    date_return = fields.Date(string='Date return',related='therapy_prescription_return_product_id.date_return', readonly=True)
    user_id = fields.Many2one('res.users', string='User',related='therapy_prescription_return_product_id.user_id', readonly=True)
    therapy_prescription_id = fields.Many2one('therapy.prescription', related='therapy_prescription_return_product_id.therapy_prescription_id', string='Therapy Prescription', readonly=True)
    therapy_record_id = fields.Many2one('therapy.record', related='therapy_prescription_return_product_id.therapy_record_id',string='Therapy Record', readonly=True)
    therapy_prescription_return_product_id = fields.Many2one('therapy.prescription.return.product',
                                                              string='Therapy Prescription Return Product')
    state = fields.Selection([('new', 'New'), ('done', 'Done')], related='therapy_prescription_return_product_id.state', string='State', readonly=True)
    @api.constrains('qty')
    def _check_qty(self):
        if not self.qty or self.qty < 0:
            raise ValidationError('Số lượng trả lại sản phẩm [%s] %s phải lớn hơn 0' % (str(self.product_id.default_code), str(self.product_id.name)))

