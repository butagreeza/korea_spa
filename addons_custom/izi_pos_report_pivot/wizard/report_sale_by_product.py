# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, RedirectWarning, except_orm, UserError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import mute_logger
import logging

class ReportSaleByProduct(models.TransientModel):
    _name = 'report.sale.by.product'

    partner_ids = fields.Many2many('res.partner', string='Partner')
    user_ids = fields.Many2many('res.users', string='User')
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")

    @api.onchange('user_ids')
    def onchange_user_ids(self):
        if self.user_ids:
            self.partner_ids = False


    def action_get_report_sale_by_product(self):
        lines = self.env['report.sale.by.product.line'].search([])
        lines.unlink()
        StockPicking_Obj = self.env['stock.picking'].sudo()
        StockMove_Obj = self.env['stock.move'].sudo()
        Partner_Obj = self.env['res.partner']
        Order_Obj = self.env['pos.order']
        Purchase_Obj = self.env['purchase.order']
        Stock_Transfer_Obj = self.env['stock.transfer']
        #todo xử lý điều kiện đầu vào
        if not self.date_from or not self.date_to:
            raise UserError('Yêu cầu nhập đủ ngày bắt đâù và ngày kết thúc!')
        stock_picking_ids = StockPicking_Obj.search([('date_done', '>=', self.date_from), ('date_done', '<=', self.date_to), ('state', '=', 'done')])
        if self.partner_ids:
            stock_picking_ids = stock_picking_ids.filtered(lambda bs: bs.partner_id.id in self.partner_ids.ids)
        else:
            if self.user_ids:
                partner_ids = Partner_Obj.search([('user_id', 'in', self.user_ids.ids)])
                stock_picking_ids = stock_picking_ids.filtered(lambda bs: bs.partner_id.id in partner_ids.ids)
        #todo xử lý dữ liệu
        vals = []
        for stock_picking_id in stock_picking_ids:
            if stock_picking_id.picking_type_id.code != 'internal':
                if stock_picking_id.picking_type_id.code == 'outgoing':
                    type = 'out'
                else:
                    type = 'in'
                for stock_move in stock_picking_id.move_lines:
                    if stock_move.product_id.x_type_card == 'none':
                        vals.append({
                            'product_id': stock_move.product_id.id,
                            'picking_id': stock_picking_id.id,
                            'type': type,
                            'origin': stock_picking_id.origin,
                            'date_done': stock_picking_id.date_done,
                            'partner_id': stock_picking_id.partner_id.id,
                            'amount': stock_move.quantity_done,

                        })
        # todo tạo phần tử cho bảng line
        # check mảng
        if len(vals) < 1:
            raise UserError('Không tìm thấy dữ liệu cho điều kiện đầu vào vừa nhập!')
        else:
            line_ids = []
            for val in vals:
                line_ids.append(self.env['report.sale.by.product.line'].create(val).id)
            # vals = dict(vals)
            # line_ids = self.env['report.sale.by.product.line'].create(vals)
            pivot_view = self.env.ref('izi_pos_report_pivot.report_sale_by_product_line_pivot_view')
            tree_view = self.env.ref('izi_pos_report_pivot.report_sale_by_product_line_tree_view')
            context = self.env.context
            if self._context.get('type') == 'tree':
                view_id = [(tree_view.id, 'tree')]
            else:
                view_id = [(pivot_view.id, 'pivot')]
            return {
                'name': _('Báo cáo bán hàng chi tiết theo sản phẩm'),
                'type': 'ir.actions.act_window',
                'res_model': 'report.sale.by.product.line',
                'views': view_id,
                'res_id': line_ids,
                'context': context,
            }


class ReportSaleByProductLine(models.TransientModel):
    _name = 'report.sale.by.product.line'

    name = fields.Char(string="Report Sale By Product")
    product_id = fields.Many2one('product.product', string='Product')
    picking_id = fields.Many2one('stock.picking', string='Picking')
    type = fields.Selection([('out', 'Out'), ('in', 'In')], string='Type', default='in')
    partner_id = fields.Many2one('res.partner', string='Partner')
    partner_name = fields.Char(related='partner_id.name', string='Name partner', store=True)
    origin = fields.Char(string="Origin")
    date_done = fields.Datetime(string='Date done')
    amount = fields.Float(string='Amount')
