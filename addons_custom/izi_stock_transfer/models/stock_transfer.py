# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, AccessError, except_orm
from odoo.osv import osv
import xlrd
import base64


class StockTransfer(models.Model):
    _name = 'stock.transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Transfer Code', track_visibility='onchange', default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('res.branch', string='Source Branch', track_visibility='onchange')
    warehouse_id = fields.Many2one('stock.warehouse', 'Source Warehouse', track_visibility='onchange')
    location_id = fields.Many2one('stock.location', 'Source Location', track_visibility='onchange')
    dest_branch_id = fields.Many2one('res.branch', string='Destination Branch', track_visibility='onchange')
    dest_warehouse_id = fields.Many2one('stock.warehouse', 'Destination Warehouse', track_visibility='onchange')
    dest_location_id = fields.Many2one('stock.location', 'Destination Location', track_visibility='onchange')
    picking_from_id = fields.Many2one('stock.picking', 'Stock picking from')
    picking_to_id = fields.Many2one('stock.picking', 'Stock picking to')

    x_compute_wh = fields.Boolean(compute='_compute_wh')
    transfer_line_ids = fields.One2many('stock.transfer.line', 'stock_transfer_id', 'Operations', track_visibility='onchange')

    scheduled_date = fields.Datetime('Scheduled Date', track_visibility='onchange', default=fields.Datetime.now)
    origin = fields.Char('Source document', track_visibility='onchange')
    note = fields.Text('Note')
    state = fields.Selection([('draft', 'Draft'), ('not_available', 'Not Available'),
                              ('ready', 'Ready'), ('transfer', 'Transfer'),('done', 'Done'), ('cancel', 'Cancel')], 'State',
                             track_visibility='onchange', default="draft")
    date_receive = fields.Datetime('Received Date')
    purchase_id = fields.Many2one('purchase.order', 'Purchase Reference')
    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")

    @api.depends('dest_warehouse_id', 'warehouse_id')
    def _compute_wh(self):
        for item in self:
            if not item.warehouse_id or not item.dest_warehouse_id or item.warehouse_id.id != item.dest_warehouse_id.id:
                item.x_compute_wh = False
            else:
                item.x_compute_wh = True

    @api.onchange('purchase_id')
    def _onchange_purchase(self):
        if self.purchase_id:
            tmp = []
            self.transfer_line_ids = False
            for line in self.purchase_id.order_line:
                argv = {
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom.id,
                    'qty': line.product_qty,
                    'name': line.name,
                }
                tmp.append(argv)
            self.transfer_line_ids = tmp
            self.origin = str(self.purchase_id.name)
            self.purchase_id = False

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        if self.warehouse_id:
            self.branch_id = self.warehouse_id.branch_id.id

    @api.onchange('dest_warehouse_id')
    def _onchange_dest_warehouse_id(self):
        if self.dest_warehouse_id:
            self.dest_branch_id = self.dest_warehouse_id.branch_id.id

    def _check_available(self):
        check_available = 0
        for line in self.transfer_line_ids:
            total_availability = self.env['stock.quant']._get_available_quantity(line.product_id, self.location_id)
            if total_availability <= 0:
                line.qty_available = 'Kh??ng c?? h??ng'
                check_available += 1
            elif total_availability < line.qty:
                line.qty_available = 'T???n: ' + str(total_availability) + ' - Kh??ng ????? h??ng'
                check_available += 1
            else:
                line.qty_available = '????? h??ng'
        if check_available != 0:
            return 'not_available'
        return 'ready'

    @api.multi
    def action_confirm(self):
        if self.state not in ('draft', 'not_available'):
            return True
        if len(self.transfer_line_ids) == 0:
            raise UserError(_('Kh??ng c?? chi ti???t d???ch chuy???n'))
        for line in self.transfer_line_ids:
            if line.qty == 0:
                raise UserError(_('B???n ch??a nh???p s??? l?????ng c???n xu???t'))
        check_available = self._check_available()
        if check_available == 'not_available':
            self.state = 'not_available'
            return True
        picking_type_from_id = self.warehouse_id.int_type_id
        if self.warehouse_id.id == self.dest_warehouse_id.id:
            if self.location_id.id == self.dest_location_id.id:
                raise UserError(_("Vui l??ng ch???n 2 ?????a ??i???m kho kh??c nhau!"))
            dest_location_id = self.dest_location_id
        else:
            if self.dest_warehouse_id.x_wh_transfer_loc_id.id == False:
                raise UserError(_("Ch??a c???u h??nh ?????a ??i???m trung chuy???n h??ng h??a trong kho. Xin h??y li??n h??? v???i ng?????i qu???n tr???"))
            dest_location_id = self.dest_warehouse_id.x_wh_transfer_loc_id
        if self.picking_from_id.id == False or self.picking_from_id.state == 'cancel':
            picking_id = self._create_picking(picking_type_from_id.id, dest_location_id.id, self.location_id.id, self.branch_id.id)
            if picking_id.id == False:
                raise UserError(_("Kh??ng x??c nh???n ???????c phi???u chuy???n kho. Xin h??y li??n h??? v???i ng?????i qu???n tr???"))
            self.update({'picking_from_id': picking_id.id})
        self.state = 'ready'

    @api.multi
    def _create_picking(self, picking_type_id, location_dest_id, location_id, branch_id, check_transfer=True):
        StockPicking = self.env['stock.picking']
        picking = False
        for transfer in self:
            if any([ptype in ['product', 'consu'] for ptype in transfer.transfer_line_ids.mapped('product_id.type')]):
                res = transfer._prepare_picking(picking_type_id, location_dest_id, location_id, branch_id)
                picking = StockPicking.create(res)
                moves = transfer.transfer_line_ids._create_stock_moves(picking, check_transfer)
                picking.message_post_with_view('mail.message_origin_link',
                                               values={'self': picking, 'origin': transfer},
                                               subtype_id=self.env.ref('mail.mt_note').id)
        return picking

    @api.model
    def _prepare_picking(self, picking_type_id, location_dest_id, location_id, branch_id):
        return {
            'picking_type_id': picking_type_id,
            'date': self.scheduled_date,
            'origin': self.name,
            'location_dest_id': location_dest_id,
            'location_id': location_id,
            'company_id': self.company_id.id,
            'branch_id': branch_id,
        }

    @api.multi
    def action_transfer(self):
        if self.state != 'ready':
            return True
        check_available = self._check_available()
        if check_available == 'not_available':
            self.state = 'not_available'
            return True
        for line in self.transfer_line_ids:
            if line.product_id.tracking != 'none':
                for item in line.lot_lines:
                    item._constraint_lot()
        self.picking_from_id.action_confirm()
        self.picking_from_id.action_assign()
        for line in self.transfer_line_ids:
            if line.product_id.tracking == 'none':
                if len(line.move_from_id.move_line_ids) != 0:
                    for m_line in line.move_from_id.move_line_ids:
                        if m_line.qty_done == 0:
                            m_line.qty_done = m_line.product_uom_qty
            else:
                for item in line.lot_lines:
                    item.location_id = self.location_id.id
                    item.dest_location_id = self.dest_location_id.id
                    if all([x.lot_id != False and x.qty_done != 0 for x in line.move_from_id.move_line_ids]) or not len(line.move_from_id.move_line_ids):
                        stock_move_out_line_vals = {
                            'product_id': line.product_id.id,
                            'origin': self.name,
                            'product_uom_id': line.product_uom.id,
                            'qty_done': item.qty_done,
                            'location_id': self.location_id.id,
                            'location_dest_id': self.dest_location_id.id,
                            'name': line.product_id.name,
                            'move_id': line.move_from_id.id,
                            'state': 'draft',
                            'picking_id': self.picking_from_id.id,
                            'lot_id': item.lot_id.id,
                            'lot_name': item.lot_id.name,
                        }
                        self.env['stock.move.line'].create(stock_move_out_line_vals)
                    else:
                        for move_line in line.move_from_id.move_line_ids:
                            if move_line.qty_done == 0 or not move_line.lot_id:
                                move_line.qty_done = item.qty_done
                                move_line.lot_id = item.lot_id.id
                                move_line.lot_name = item.lot_id.name
                                break
        for line in self.transfer_line_ids:
            if line.product_id.tracking != 'none':
                if line.qty_done < line.qty:
                    raise except_orm(_('Th??ng b??o'), _(
                        'B???n ch??a nh???p ????? chi ti???t s??? l??/serial cho s???n ph???m "%s". Vui l??ng c???p nh???t th??m ????? ho??n th??nh ????n!' % line.product_id.name))
                elif line.qty_done > line.qty:
                    raise except_orm(_('Th??ng b??o'), _(
                        'B???n ???? nh???p chi ti???t s??? l??/serial l???n h??n s??? l?????ng d???ch chuy???n ban ?????u. Chi ti???t s???n ph???m "%s".' % line.product_id.name))
        self.picking_from_id.button_validate()
        if not self.picking_from_id.state == 'done':
            raise except_orm(_('Th??ng b??o'), _('G???p v???n ????? ??? ????n d???ch chuy???n kho. Vui l??ng li??n h??? qu???n tr??? vi??n'))
        if self.warehouse_id.id == self.dest_warehouse_id.id:
            self.state = 'done'
        else:
            self.state = 'transfer'

    @api.multi
    def action_receive(self):
        if self.state != 'transfer':
            return True
        picking_type_to_id = self.dest_warehouse_id.int_type_id
        picking_id = self._create_picking(picking_type_to_id.id, self.dest_location_id.id, self.dest_warehouse_id.x_wh_transfer_loc_id.id,
                                          self.dest_branch_id.id, False)
        if picking_id.id == False:
            raise UserError(_("Kh??ng x??c nh???n ???????c phi???u chuy???n kho. Xin h??y li??n h??? v???i ng?????i qu???n tr???"))
        self.update({'picking_to_id': picking_id.id, 'date_receive': fields.Datetime.now()})
        picking_id.action_confirm()
        if self.picking_to_id.state == 'done':
            self.state = self.picking_to_id.state
        else:
            self.picking_to_id.action_assign()
            for line in self.transfer_line_ids:
                if line.product_id.tracking == 'none':
                    if len(line.move_to_id.move_line_ids) != 0:
                        for m_line in line.move_to_id.move_line_ids:
                            if m_line.qty_done == 0:
                                m_line.qty_done = m_line.product_uom_qty
                else:
                    for item in line.lot_lines:
                        item.location_id = self.location_id.id
                        item.dest_location_id = self.dest_location_id.id
                        if all([x.lot_id != False and x.qty_done != 0 for x in line.move_to_id.move_line_ids]) or not len(line.move_to_id.move_line_ids):
                            stock_move_out_line_vals = {
                                'product_id': line.product_id.id,
                                'origin': self.name,
                                'product_uom_id': line.product_uom.id,
                                'qty_done': item.qty_done,
                                'location_id': self.location_id.id,
                                'location_dest_id': self.dest_location_id.id,
                                'name': line.product_id.name,
                                'move_id': line.move_to_id.id,
                                'state': 'draft',
                                'picking_id': picking_id.id,
                                'lot_id': item.lot_id.id,
                                'lot_name': item.lot_id.name,
                            }
                            self.env['stock.move.line'].create(stock_move_out_line_vals)
                        else:
                            for move_line in line.move_to_id.move_line_ids:
                                if move_line.qty_done == 0 or not move_line.lot_id:
                                    move_line.qty_done = item.qty_done
                                    move_line.lot_id = item.lot_id.id
                                    move_line.lot_name = item.lot_id.name
                                    break
            self.picking_to_id.button_validate()
            self.state = 'done'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.transfer') or _('New')
        return super(StockTransfer, self).create(vals)

    @api.multi
    def unlink(self):
        if self.state == 'draft':
            return super(StockTransfer, self).unlink()
        raise except_orm(_('Th??ng b??o'), ('B???n ch??? c?? th??? x??a khi ??? tr???ng th??i Nh??p'))

    @api.multi
    def action_back(self):
        if self.picking_from_id:
            self.picking_from_id.action_cancel()
            self.picking_from_id.unlink()
        self.state = 'draft'

    @api.multi
    def action_cancel(self):
        if self.picking_from_id:
            self.picking_from_id.action_cancel()
        self.state = 'cancel'

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    @api.multi
    def action_import_line(self):
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise osv.except_osv("C???nh b??o!",
                                     (
                                         "File kh??ng ???????c t??m th???y ho???c kh??ng ????ng ?????nh d???ng. Vui l??ng ki???m tra l???i ?????nh d???ng file .xls ho???c .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 3
            lines = []
            while index < sheet.nrows:
                product_code = sheet.cell(index, 1).value
                product_id = False
                uom_id = False
                lot_id = False
                lot_line = []
                product_obj = self.env['product.product'].search([('default_code', '=', product_code)],limit=1)
                if product_obj.id == False:
                    raise except_orm('C???nh b??o!',
                                     ("Kh??ng t???n t???i s???n ph???m c?? m?? " + str(
                                         product_code) + ". Vui l??ng ki???m tra l???i d??ng " + str(
                                         index + 1)))
                product_id = product_obj.id
                uom_id = product_obj.product_tmpl_id.uom_id.id
                qty = sheet.cell(index, 4).value
                lot_name = sheet.cell(index, 5).value.strip().upper()
                if lot_name:
                    life_date = sheet.cell(index, 6).value
                    lot_id = self.env['stock.production.lot'].search([('name', 'like', lot_name),('product_id','=',product_id)],limit=1)
                    if lot_id.id == False:
                        lot_id = self.env['stock.production.lot'].create({
                            'name': lot_name,
                            'product_id': product_id,
                            'life_date': life_date,
                            'product_uom_id': uom_id})
                    line_argv = {
                        'location_id': self.location_id.id,
                        'dest_location_id': self.dest_location_id.id,
                        'uom_id': uom_id,
                        'lot_id':lot_id.id,
                        'lot_name':lot_name,
                        'life_date':life_date,
                        'qty_done': qty,
                        'product_id': product_id,
                    }
                    lot_line.append(line_argv)
                note = sheet.cell(index, 7).value
                if all([x['product_id'] != product_id for x in lines]) or len(lines) == 0:
                    argvs = {
                        'product_id': product_id,
                        'product_uom': uom_id,
                        'qty': qty,
                        'note': note,
                        'lot_lines':lot_line
                    }
                    lines.append(argvs)
                else:
                    for dict in lines:
                        if dict['product_id'] == product_id:
                            dict['qty'] += qty
                            for l in lot_line:
                                dict['lot_lines'].append(l)
                index = index + 1
            self.transfer_line_ids = lines
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    @api.multi
    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/izi_stock_transfer/static/template/import_izi_stock_transfer.xlsx',
            "target": "_parent",
        }


    @api.multi
    def action_print(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/izi_stock_transfer.report_template_stock_picking_internal_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }


class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args += [('name', 'ilike', name)]
        res = self.search(args, limit=limit)

        return res.name_get()