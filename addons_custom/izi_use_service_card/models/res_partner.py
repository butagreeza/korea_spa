# -*- coding: utf-8 -*-
from odoo import models, api, fields , _
from odoo.exceptions import except_orm
from odoo.osv import expression
from odoo import sys, os
import base64, time
from os.path import  join
from datetime import datetime, timedelta
import logging


class ResPartnerCustom(models.Model):
    _inherit = 'res.partner'
    # x_first_date_use_service = fields.Date(string='First Date Use Service', compute='_compute_first_date', store=True)
    # x_end_date_use_service = fields.Date(string='End Date Use Service', compute='_compute_first_date', store=True)
    x_first_date_use_service = fields.Date(string='First Date Use Service', compute='_compute_first_date')
    x_end_date_use_service = fields.Date(string='End Date Use Service', compute='_compute_first_date')

    # @api.depends('x_first_date_use_service')
    def _compute_first_date(self):
        for detail in self:
            order_ids = self.env['pos.order'].search([('partner_id', '=', detail.id)], order='date_order')
            for line in order_ids:
                detail.x_first_date_use_service = line.date_order
                break
            break

        for detail in self:
            order_ids = self.env['pos.order'].search([('partner_id', '=', detail.id)], order='date_order DESC')
            for line in order_ids:
                detail.x_end_date_use_service = line.date_order
                break
            break

    @api.model
    def get_card_detail_customer(self, partner_id):
        # print(1)
        card_details = []
        if partner_id:
            # use_card_line_obj = self.env['izi.service.card.using'].sudo().search(
            #     [('customer_id', '=', partner_id), ('type', '!=', 'card')], order='id desc')
            # for use_card_line_ids in use_card_line_obj:
            #     for use_card_line_id in use_card_line_ids.service_card1_ids:
            #         employee = ''
            #         for x in use_card_line_id.employee_ids:
            #             employee = employee + ', ' + str(x.name)
            #         for y in use_card_line_id.doctor_ids:
            #             employee = employee + ', ' + str(y.name)
            #         vals3 = {
            #             'order_name': use_card_line_ids.pos_order_id.name if use_card_line_ids.pos_order_id else '',
            #             'redeem_date': datetime.strptime(use_card_line_id.using_id.redeem_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7),
            #             'service_name': use_card_line_id.service_id.name,
            #             'quantity': use_card_line_id.quantity,
            #             'uom_name': use_card_line_id.uom_id.name,
            #             'employee': employee[1:] if employee else '',
            #             'using_name': use_card_line_id.using_id.name,
            #             'serial_name': use_card_line_id.serial_id.name if use_card_line_id.serial_id else '',
            #             'price_unit': int(use_card_line_id.price_unit),
            #             'state': use_card_line_ids.state,
            #             'customer_sign': use_card_line_id.using_id.signature_image,
            #             'note': use_card_line_id.note if use_card_line_id.note else '',
            #             'type': use_card_line_id.using_id.type,
            #             'using_id': use_card_line_ids.id,
            #         }
            #         card_details.append(vals3)
            service_card_using_lines = self.env['izi.service.card.using.line'].sudo().search([
                ('using_id.customer_id', '=', partner_id), ('type', '!=', 'service_card')
            ], order='id desc')
            if service_card_using_lines:
                for use_card_line_id in service_card_using_lines:
                    employee = ''
                    for x in use_card_line_id.employee_ids:
                        employee = employee + ', ' + str(x.name)
                    for y in use_card_line_id.doctor_ids:
                        employee = employee + ', ' + str(y.name)

                    if use_card_line_id.using_id.type == 'service':
                        service_card_using_line_type = 'Dịch vụ lẻ'
                    elif use_card_line_id.using_id.type == 'bundle':
                        service_card_using_line_type = 'Gói liệu trình'
                    elif use_card_line_id.using_id.type == 'guarantee_bundle':
                        service_card_using_line_type = 'Bảo hành gói liệu trình'
                    elif use_card_line_id.using_id.type == 'guarantee':
                        service_card_using_line_type = 'Bảo hành'
                    else:
                        service_card_using_line_type = use_card_line_id.type

                    vals3 = {
                        'order_name': use_card_line_id.using_id.pos_order_id.name if use_card_line_id.using_id.pos_order_id else '',
                        'redeem_date': datetime.strptime(use_card_line_id.using_id.redeem_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7),
                        'service_name': use_card_line_id.service_id.name,
                        'quantity': use_card_line_id.quantity,
                        'uom_name': use_card_line_id.uom_id.name,
                        'employee': employee[1:] if employee else '',
                        'using_name': use_card_line_id.using_id.name,
                        'serial_name': use_card_line_id.serial_id.name if use_card_line_id.serial_id else '',
                        'price_unit': int(use_card_line_id.price_unit),
                        'state': use_card_line_id.using_id.state,
                        'customer_sign': use_card_line_id.using_id.signature_image,
                        'note': use_card_line_id.note if use_card_line_id.note else '',
                        'type': service_card_using_line_type,
                        'using_id': use_card_line_id.using_id.id,
                    }
                    card_details.append(vals3)
            lot = self.env['stock.production.lot'].sudo().search([('x_customer_id', '=', partner_id)], order='id desc')
            for index in lot:
                for line in index:
                    use_card_line_obj = self.env['izi.service.card.using.line'].sudo().search(
                        [('serial_id', '=', line.id)], order='id desc')
                    for use_card_line_id in use_card_line_obj:
                        employee = ''
                        for x in use_card_line_id.employee_ids:
                            employee = employee + ', ' + str(x.name)
                        for y in use_card_line_id.doctor_ids:
                            employee = employee + ', ' + str(y.name)
                        vals3 = {
                            'redeem_date': datetime.strptime(use_card_line_id.using_id.redeem_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7),
                            'service_name': use_card_line_id.service_id.name,
                            'quantity': use_card_line_id.quantity,
                            'uom_name': use_card_line_id.uom_id.name,
                            'employee': employee[1:] if employee else '',
                            'using_name': use_card_line_id.using_id.name,
                            'serial_name': use_card_line_id.serial_id.name if use_card_line_id.serial_id else '',
                            'price_unit': int(use_card_line_id.price_unit),
                            'state': use_card_line_id.using_id.state,
                            'customer_sign': use_card_line_id.using_id.signature_image,
                            'note': use_card_line_id.note if use_card_line_id.note else '',
                            'type': 'Thẻ dịch vụ',
                            'using_id': use_card_line_id.using_id.id,
                        }
                        card_details.append(vals3)

        def custom_sort(elem):
            return elem['using_id']

        card_details.sort(key=custom_sort,reverse=True)
        return card_details