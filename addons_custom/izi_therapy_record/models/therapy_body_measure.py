# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError, MissingError


class TherapyBodyMeasure(models.Model):
    _name = 'therapy.body.measure'

    name = fields.Char(string='Name')
    measurement_time = fields.Datetime(string='Measurement  time', default=lambda self: fields.Datetime.now())  # Thời gian đo
    technician = fields.Many2one('hr.employee', string='Technician')  # Kỹ thuật viên
    note = fields.Text(string='Note')
    therapy_record_id = fields.Many2one('therapy.record', string='Therapy Record')
    body_measure_line_ids = fields.One2many('therapy.body.measure.line', 'body_measure_id', string='Therapy Body Measure Line')
    product_id = fields.Many2one('product.product', string='Product')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if vals['therapy_record_id']:
                partner_id = self.env['therapy.record'].search([('id', '=', vals['therapy_record_id'])]).partner_id.id
                array_date = vals['measurement_time'].split(' ')[0].split('-')
                measurement_time = str(array_date[2]) + str(array_date[1]) + str(array_date[0])
                vals['name'] = 'CSGB_' + str(partner_id) + '_' + measurement_time
        return super(TherapyBodyMeasure, self).create(vals)

    @api.onchange('product_id')
    def constrains_product_id(self):
        if self.product_id:
            if not self.product_id.x_body_area_measure_ids:
                raise UserError('Bạn chưa cấu hình thông số đo cho dịch vụ %s' % self.product_id.name)
            arr_body_measure = []
            for body_area in self.product_id.x_body_area_measure_ids:
                line_id = self.env['therapy.body.measure.line'].create({
                    'body_measure_id': self.id,
                    'body_area_id': body_area.id,
                    'measurement': 0,
                })
                arr_body_measure.append(line_id.id)
            self.body_measure_line_ids = [(6, 0, arr_body_measure)]


class TherapyBodyMeasureLine(models.Model):
    _name = 'therapy.body.measure.line'

    name = fields.Char(string='Name')
    body_measure_id = fields.Many2one('therapy.body.measure', string='Therapy Body Measure')
    body_area_id = fields.Many2one('body.area', string='Body Area')
    measurement = fields.Float(string='Measurement')
