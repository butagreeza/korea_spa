# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, except_orm


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        Warehouse = self.env['stock.warehouse']
        branch = self.env.user.branch_id
        # if not branch: raise except_orm('ngadv', 'ngadv')
        if not branch: raise except_orm('Thông báo', 'Tài khoản người dùng của bạn chưa chọn chi nhánh, không thể mua hàng.')

        warehouses = Warehouse.search([('branch_id', '=', branch.id)])
        if len(warehouses) > 1:
            str_warehouses = ''
            for warehouse in warehouses:
                str_warehouses += '%s,' % (str(warehouse.name))
            raise except_orm('Thông báo', 'Tài khoản người dùng của bạn đang chịu tránh nhiệm chi nhánh %s, '
                             'chi nhánh này đang tham chiếu đến %s kho (%s), '
                             'vui lòng kiểm tra lại' % (str(branch.name), str(len(warehouses), str(str_warehouses))))
        if not warehouses:
            raise except_orm('Thông báo', 'Tài khoản người dùng của bạn đang chịu trách nhiệm chi nhánh %s, chi nhánh đó đang không tham chiếu đến kho nào!' % (str(branch.name)))
        return warehouses.in_type_id

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=READONLY_STATES, required=True, default=_default_picking_type, help="This will determine operation type of incoming shipment")

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step'\
                    or (order.company_id.po_double_validation == 'two_step'\
                        and order.amount_total < self.env.user.company_id.currency_id.compute(order.company_id.po_double_validation_amount, order.currency_id))\
                    or order.user_has_groups('purchase.group_purchase_manager') or order.user_has_groups('izi_res_permissions.group_leader_accountant'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    quantity = fields.Float(string='On Hand', compute='_onchange_quantity')

    @api.depends('product_id')
    def _onchange_quantity(self):
        for product in self:
            if product.product_id:
                product.quantity = product.product_id.product_tmpl_id.qty_available
