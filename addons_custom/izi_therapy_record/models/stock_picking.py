# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import UserError, ValidationError, MissingError
import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_therapy_prescription_id = fields.Many2one('therapy.prescription', string='Therapy Prescription')
    x_therapy_record_id = fields.Many2one('therapy.record', related='x_therapy_prescription_id.therapy_record_id', string='Therapy Record', store=True, readonly=True)
    x_medicine_day_ok = fields.Boolean(string='Medicine Day')
    return_product_id = fields.Many2one('therapy.prescription.return.product', string='Return Product')

    def create_activity_history(self):
        pass

    @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        if self.x_therapy_record_id and self.x_therapy_prescription_id.state_picking == 'open':
            #todo trừ tồn trên HSTL
            for move_line in self.move_lines.filtered(lambda move: move.quantity_done !=0):
                qty_move = move_line.quantity_done
                for record_product_id in self.x_therapy_record_id.therapy_record_product_ids.filtered(lambda remain: remain.product_id.id == move_line.product_id.id):
                    qty_prescription = 0
                    for product_prescription in self.env['therapy.prescription.line'].search([('product_id', '=', record_product_id.product_id.id), ('order_id', '=', record_product_id.order_id.id), ('therapy_prescription_id', '=', self.x_therapy_prescription_id.id), ('type', '!=', 'guarantee')]):
                        if product_prescription.order_line_id == record_product_id.order_line_id:
                            qty_prescription = product_prescription.qty
                    if qty_prescription == 0:
                        continue
                    if qty_move <= qty_prescription:
                        record_product_id.qty_used = record_product_id.qty_used + qty_move
                        continue
                    else:
                        record_product_id.qty_used = record_product_id.qty_used + qty_prescription
                        qty_move -= qty_prescription
            #todo trừ tồn số ngày thuốc
            record_product_medicine_ids = self.x_therapy_record_id.therapy_record_product_ids.filtered(
                lambda remain: remain.product_id.x_is_medicine_day)
            for record_product_medicine_id in record_product_medicine_ids:
                qty = 0
                if record_product_medicine_id and self.x_medicine_day_ok:
                    for line_remain_id in self.x_therapy_prescription_id.therapy_prescription_line_remain_ids.filtered(
                            lambda
                                    line: line.product_id.x_is_medicine_day and line.product_id.id == record_product_medicine_id.product_id.id):
                        if line_remain_id.order_line_id.id == record_product_medicine_id.order_line_id.id and line_remain_id.order_id.id == record_product_medicine_id.order_id.id:
                            qty += line_remain_id.qty
                    record_product_medicine_id.qty_used += qty
            #todo cập nhật ngày hết thuốc trên hstl và sinh lịch nhắc
            self.create_activity_history()
            self.x_therapy_prescription_id.state_picking = 'close'
        return res

    @api.multi
    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        # if self.picking_type_id.code == 'incoming':
        #     therapy_record_product_ids = self.env['therapy.record.product'].search([('therapy_record_id', '=', self.x_therapy_record_id.id)])
        #     for therapy_record_product in therapy_record_product_ids:
        #         for move in self.move_lines:
        #             if therapy_record_product.product_id == move.product_id:
        #                 therapy_record_product.qty_used -= move.quantity_done
        #                 if therapy_record_product.qty_used < 0:
        #                     therapy_record_product.qty_used = 0
        if self.return_product_id:
            self.return_product_id.state = 'done'
        return res

class StockMove(models.Model):
    _inherit = 'stock.move'

    x_therapy_prescription_id = fields.Many2one('therapy.prescription', string='Therapy Prescription')
    x_therapy_record_id = fields.Many2one('therapy.record', related='x_therapy_prescription_id.therapy_record_id', string='Therapy Record', store=True, readonly=True)
    x_is_product_remain = fields.Boolean(string='Is product Remain', default=False)
    x_is_product_guarantee = fields.Boolean(string='Is product guarantee', default=False)
    x_order_line_id = fields.Many2one('pos.order.line', string='Pos Order Line')
    x_order_id = fields.Many2one('pos.order', string='Pos Order')
