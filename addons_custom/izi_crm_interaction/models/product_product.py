# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_service_remind_ids = fields.One2many('product.service.remind', 'product_id', string="Remind Service")
    x_is_remind = fields.Boolean(string="Is remind", default=False)

    def get_config_remind(self, remind_configs):
        arr_remind_config = []
        for remind_config in remind_configs:
            arr_remind_config.append({
                'activity_type_id': remind_config.activity_type_id.id,
                'date_number': remind_config.date_number,
                'object': remind_config.object,
                'repeat': remind_config.repeat,
                'period': remind_config.period,
                'type': remind_config.type,
                'note': remind_config.note
            })
        return arr_remind_config
