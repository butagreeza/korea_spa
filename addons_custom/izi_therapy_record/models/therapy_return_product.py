# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError, MissingError, except_orm


class TherapyPrescriptionReturnProduct(models.Model):
    _name = 'therapy.prescription.return.product'
    _rec_name = 'therapy_prescription_id'
    _description = u'Therapy Prescription Return Product'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    therapy_prescription_id = fields.Many2one('therapy.prescription', string='Therapy Prescription', track_visibility='onchange')
    therapy_record_id = fields.Many2one('therapy.record', string='Therapy Record', track_visibility='onchange')
    date_return = fields.Date(string='Date return', default=date.today(), track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='User', track_visibility='onchange')
    state = fields.Selection([('draft', 'Draft'), ('to_approve', 'To Approve'), ('waiting_warehouse', 'Waiting Warehouse'), ('done', 'Done'), ('cancel', 'Cancel')], default='draft', track_visibility='onchange')
    therapy_prescription_return_product_line_ids = fields.One2many('therapy.prescription.return.product.line',
                                                                   'therapy_prescription_return_product_id',
                                                                   string='Therapy Prescription Return Product Line')
    partner_id = fields.Many2one('res.partner', string='Partner', track_visibility='onchange')
    picking_id = fields.Many2one('stock.picking', string='Picking', track_visibility='onchange')

    @api.model
    def create(self, vals):
        if vals.get('therapy_record_id'):
            return_product = self.env['therapy.prescription.return.product'].search([('therapy_record_id', '=', vals.get('therapy_record_id')), ('state', '=', 'draft')])
            if return_product:
                raise except_orm('Cảnh báo!', (
                        "Đang có %s đơn trả hàng ở trạng thái mới. Liên hệ Admin để được giải quyết hoặc tải lại trang.Xin cám ơn!" % len(return_product)))
        return super(TherapyPrescriptionReturnProduct, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('therapy_prescription_id'):
            return_product = self.env['therapy.prescription.return.product'].search(
                [('therapy_prescription_id', '=', vals.get('therapy_prescription_id')), ('state', '=', 'draft')])
            if return_product:
                raise except_orm('Cảnh báo!', (
                        "Đang có %s đơn trả hàng ở trạng thái mới. Liên hệ Admin để được giải quyết hoặc tải lại trang.Xin cám ơn!" % len(return_product)))
        return super(TherapyPrescriptionReturnProduct, self).write(vals)

    @api.multi
    def action_confirm(self):
        for detail in self.therapy_record_id:
            if detail.state != 'in_therapy':
                raise except_orm('Cảnh báo!', ("Hồ sơ trị liệu không còn ở trạng thái trong liệu trình, vui lòng kiểm tra lại để tiếp tục!"))
            query = """
                        SELECT id FROM therapy_prescription_return_product
                        WHERE therapy_record_id = %s
                        AND state = 'draft'
                        """
            self._cr.execute(query, ([self.therapy_record_id.id]))
            res = self._cr.dictfetchall()
            if len(res) > 1:
                raise except_orm('Cảnh báo!', (
                            "Đang có %s đơn trả hàng ở trạng thái mới. Liên hệ Admin để được giải quyết hoặc tải lại trang.Xin cám ơn!" % len(res)))

    @api.multi
    def send_return_product(self):
        for detail in self:
            detail.state = 'to_approve'

    @api.multi
    def action_confirm_return_product(self):
        for detail in self:
            detail.state = 'waiting_warehouse'
        arr_product_stocks = []
        for therapy_prescription_return_product in self.therapy_prescription_return_product_line_ids:
            if therapy_prescription_return_product not in arr_product_stocks:
                arr_product_stocks.append(therapy_prescription_return_product)
        Picking = self.env['stock.picking']
        Move = self.env['stock.move']
        picking_type_id = self.env.user.x_pos_config_id.picking_type_id.return_picking_type_id
        if not picking_type_id:
            raise UserError(_('Chưa cấu hình loại điều chuyển kho cho điểm bán hàng của bạn!'))
        if self.partner_id:
            destination_id = self.partner_id.property_stock_customer.id

        picking_vals = {
            'origin': self.therapy_record_id.name,
            'partner_id': self.partner_id.id,
            'scheduled_date': fields.Datetime.now(),
            'picking_type_id': picking_type_id.id,
            'move_type': 'direct',
            'location_id': destination_id,
            'location_dest_id': picking_type_id.default_location_dest_id.id,
            'x_therapy_record_id': self.therapy_record_id.id,
            'return_product_id': self.id
        }
        picking_id = Picking.create(picking_vals)
        for arr_product_stock in arr_product_stocks:
            Move.create({
                'name': self.therapy_record_id.name,
                'product_uom': arr_product_stock['uom_id'].id,
                'picking_id': picking_id.id,
                'picking_type_id': picking_type_id.id,
                'product_id': arr_product_stock['product_id'].id,
                'product_uom_qty': arr_product_stock['qty'],
                'location_id': destination_id,
                'location_dest_id': picking_type_id.default_location_dest_id.id,
                'x_therapy_record_id': self.therapy_record_id.id,
            })
        self.picking_id = picking_id.id

    @api.multi
    def set_to_draft(self):
        for detail in self:
            if detail.state == 'to_approve':
                detail.state = 'draft'
            elif detail.state == 'waiting_warehouse':
                detail.state = 'draft'
                detail.picking_id.unlink()
            else:
                detail.state = 'draft'
                for line in detail.therapy_prescription_return_product_line_ids:
                    stock_quant = self.env['stock.quant'].search([('product_id', '=', line.product_id.id), ('location_id', '=', self.picking_id.picking_type_id.default_location_dest_id.id)])
                    if not stock_quant:
                        raise ValidationError('Bạn chưa cấu hình xuất từ kho nào!')
                    else:
                        stock_quant.quantity -= line.qty
                        detail.picking_id.action_cancel_picking()
                        detail.picking_id.action_set_to_draft()
                        detail.picking_id.unlink()

class TherapyPrescriptionReturnProductLine(models.Model):
    _name = 'therapy.prescription.return.product.line'

    product_id = fields.Many2one('product.product', string='Product')
    qty = fields.Float(string='Quantity')
    uom_id = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure', readonly=1)
    date_return = fields.Date(string='Date return',related='therapy_prescription_return_product_id.date_return', readonly=True)
    user_id = fields.Many2one('res.users', string='User',related='therapy_prescription_return_product_id.user_id', readonly=True)
    therapy_prescription_id = fields.Many2one('therapy.prescription', related='therapy_prescription_return_product_id.therapy_prescription_id', string='Therapy Prescription', readonly=True)
    therapy_record_id = fields.Many2one('therapy.record', related='therapy_prescription_return_product_id.therapy_record_id',string='Therapy Record', readonly=True)
    partner_id = fields.Many2one('res.partner', related='therapy_prescription_return_product_id.partner_id',string='Partner', readonly=True)
    therapy_prescription_return_product_id = fields.Many2one('therapy.prescription.return.product',
                                                              string='Therapy Prescription Return Product')
    state = fields.Selection([('draft', 'Draft'), ('to_approve', 'To Approve'), ('waiting_warehouse', 'Waiting Warehouse'), ('done', 'Done')], default='draft', related='therapy_prescription_return_product_id.state', string='State', readonly=True)

    @api.constrains('qty')
    def _check_qty(self):
        if not self.qty or self.qty < 0:
            raise ValidationError('Số lượng trả lại sản phẩm [%s] %s phải lớn hơn 0' % (str(self.product_id.default_code), str(self.product_id.name)))

