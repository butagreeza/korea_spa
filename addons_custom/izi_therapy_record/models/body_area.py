
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import UserError, ValidationError, MissingError


class BodyArea(models.Model):
    _name = 'body.area'
    _order = 'name desc'

    name = fields.Char(string="Name Area")
    code = fields.Char(string="Code")
    type = fields.Selection([('injection', 'Area Injection'), ('measure', 'Area Measure')], string='Type Area')
    body_inject_id = fields.Many2one('product.product', string='Body Injection')
    body_measure_id = fields.Many2one('product.product', string='Body Measure')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if self._context.get('default_product_id'):
            product_id = self.env['product.product'].search([('id', '=', self._context.get('default_product_id'))], limit=1)
            domain = []
            arr_body = []
            if product_id :
                if product_id.x_is_injection:
                    arr_body = product_id.x_body_area_inject_ids.ids
                elif product_id.x_is_injection and self._context.get('is_measure'):
                    arr_body = product_id.x_body_area_measure_ids.ids
                elif product_id.x_is_massage:
                    if self._context.get('therapy_record_id'):
                        therapy_product_ids = self.env['therapy.record.product'].search(
                            [('therapy_record_id', '=', self._context.get('therapy_record_id'))])
                        order_id = self.env['pos.order'].search([('id', '=', self._context.get('order_id'))])
                        for line_id in therapy_product_ids.filtered(
                                lambda line: line.product_id.x_is_injection and line.order_id.id == order_id.id):
                            arr_body += line_id.body_area_ids.filtered(
                                lambda body: body.id in product_id.x_body_area_massage_ids.ids).ids
                    else:
                        arr_body = product_id.x_body_area_massage_ids.ids
                else:
                    arr_body = []
            if len(arr_body) == 0:
                raise UserError('Bạn chưa cấu hình vùng cơ thể cho dịch vụ %s. Vui lòng vào cấu hình trước khi thao tác! Xin cám ơn.' % product_id.name)
            domain = [('name', operator, name), ('id', 'in', arr_body)] + args
            return self.env['body.area'].search(domain).name_get()
        return super(BodyArea, self).name_search(name, args, operator, limit)
