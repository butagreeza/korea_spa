# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_is_massage = fields.Boolean('Is Massage', default=False)
    x_is_injection = fields.Boolean('Is Injection', default=False)
    x_is_medicine_day = fields.Boolean(string='IS Medicine', default=False)
    x_body_area_inject_ids = fields.Many2many('body.area', 'body_inject_id', domain=[('type', '=', 'injection')], string='Body Area Inject')
    x_body_area_measure_ids = fields.Many2many('body.area', 'body_measure_id', domain=[('type', '=', 'measure')], string='Body Area Measure')
    x_body_area_massage_ids = fields.Many2many('body.area', 'body_inject_id', domain=[('type', '=', 'injection')], string='Body Area Massage')