# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import except_orm, ValidationError, UserError
from odoo.osv import expression
from odoo import sys, os
import base64, time
from os.path import join
from datetime import datetime, date, timedelta
import logging, re
from odoo import http
from lxml import etree
from odoo.osv.orm import setup_modifiers
from dateutil.relativedelta import relativedelta
import requests
import json

import logging
# import scrapy
# from scrapy import Spider
# from scrapy.selector import Selector
# from crawler.items import CrawlerItem

_logger = logging.getLogger(__name__)

class HotlineConfig(models.Model):
    _name = 'hotline.config'

    name = fields.Char(string="Voip Phonecall Config")
    phone = fields.Char(string="Phone")
    active = fields.Boolean(string="Active", default=True)
    date_start_synchronize = fields.Datetime(string="Date start synchronize")
    date_end_synchronize = fields.Datetime(string="Date end synchronize", default=lambda self: fields.Datetime.now())
    key_access = fields.Char(string="Key Access")



class Phonecall(models.Model):
    _name = "phonecall"

    name = fields.Char(string="Phone Call")
    call_type = fields.Selection([('outgoing', 'Gọi ra'), ('incoming', 'Gọi vào')])
    call_date = fields.Datetime(string="Call date")
    phone = fields.Char(string="Phone")
    partner_id = fields.Many2one('res.partner', compute='_compute_partner', store='True', string="Partner")
    user_id = fields.Many2one('res.users', string="User")
    user_ids = fields.Many2many('res.users', string='Users')
    call_status = fields.Selection([('miss', 'Cuộc gọi nhỡ '), ('meetAgent', 'Cuộc gọi gặp')], string="Call status")
    path_download = fields.Char("File download")
    path = fields.Char('Link recording')
    voip_phonecall_config_id = fields.Many2one('voip.phonecall.config', string='Voip Phonecall Config')
    hotline = fields.Char(string='Hotline')
    hold_time = fields.Float(string='Time Hold')
    wait_time = fields.Float(string='Time Wait')
    talk_time = fields.Float(string='Time Talk')
    end_time = fields.Datetime(string="End time")
    start_time = fields.Datetime(string="Start time")
    end_status = fields.Selection([('system', 'Hệ thống'), ('cus', 'Khách hàng')])
    branch_hotline = fields.Char(string="Branch Hotline")
    customer_3c_id = fields.Char(string="Customer ID")
    mobifone_id = fields.Char(string="Mobiphone ID")
    agent_text = fields.Text(string='Agent')
    many_agent_text = fields.Text(string='Many Agent')

    @api.model
    def get_recoding_file(self):
        self.refresh()
        # todo connect_to_ccal
        voip_phonecall_Obj = self.env['hotline.config'].search([('active', '=', True)])

        dem = 0
        for phone_config in voip_phonecall_Obj:
            if not phone_config.date_end_synchronize:
                end = (datetime.now() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
                time_end = f"&start_time_to={end}"
            else:
                end = (datetime.strptime(phone_config.date_end_synchronize,"%Y-%m-%d %H:%M:%S") + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
                time_end = f"&start_time_to={end}"
            start = (datetime.strptime(phone_config.date_start_synchronize,"%Y-%m-%d %H:%M:%S") + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
            phone = phone_config.phone
            check = True
            page = 1
            #todo 3c tối đa số lượng trả về là 500 bản ghi 1 lần đồng bộ nên phải lặp lại việc đồng bộ với các page khác nhau
            while check == True:
                url = "https://3c-api1.mobifone.vn/{0}/api/v1/calls?start_time_since={1}{2}&count=500&page={3}&order_by=start_time&order_type=asc".format(phone, start, time_end, page)
                payload = {}
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {phone_config.key_access}',
                    'Cookie': 'laravel_session=eyJpdiI6Im9qNHNOZ0lcL3lWTFNYTm9LNEFaMld3PT0iLCJ2YWx1ZSI6ImQ4ZStiOXZTOWV4UGt0K2lqOHVwNWNGb2RDMVZcL0Qxdll6ZTByejE2SmU3VGdTXC9CSWtPVlwvd3NnY2FYNDV2RGd0ZWI0YjVKU1pna1JtdFFLQUZDU0VBPT0iLCJtYWMiOiJjNjEwM2IxNjg5YjZhZTg4OTI0NjAwNjcyNzBiNzZlYzYyNzhjY2Y0ZjU3YmFlMDcxMzYwYTFjZjQyMTkwMWM5In0%3D; expires=Thu, 31-Jul-2025 08:23:26 GMT; Max-Age=155520000; path=/; httponly'
                }
                response = requests.request("GET", url, headers=headers, data=payload, allow_redirects=False)
                if response.status_code != 200:
                    break
                # todo convert json data to dictionary
                json_cdr = json.loads(response.content)
                contents = json_cdr['calls']
                if len(contents) == 0:
                    check = False
                count = 0
                dem_1 = 0
                for list_content in contents:
                    count += 1
                    time_start = (datetime.strptime(list_content['start_time'], "%Y-%m-%d %H:%M:%S") - timedelta(
                        hours=7)).strftime("%Y-%m-%d %H:%M:%S")
                    # todo check trùng bản ghi
                    voip_ids = self.env['phonecall'].search(
                        [('customer_3c_id', '=', str(list_content['customer_id'])), ('call_date', '=', time_start),
                         ('mobifone_id', '=', str(list_content['id']))])
                    for voip_id in voip_ids:
                        if not voip_id.partner_id:
                            voip_id._compute_partner()
                        else:
                            if not voip_id.partner_id.x_call_last_date or voip_id.partner_id.x_call_last_date < voip_id.start_time:
                                voip_id.partner_id.x_call_last_date = voip_id.start_time
                    if not voip_ids:
                        if list_content['call_type'] == 1:
                            call_type = 'outgoing'
                            name = 'Call in'
                        else:
                            call_type = 'incoming'
                            name = 'Call out'
                        # partner_id = self.env['res.partner'].search([('phone', '=', list_content['caller'])])
                        phone_switchboard = phone
                        arr_user_id = list_content['agent_id'].split(',')
                        user_ids = self.env['res.users'].search([('x_agent_phone', 'in', arr_user_id)])
                        user_last_id = self.env['res.users'].search(['|', ('x_agent_phone', '=', list_content['last_agent_id']), ('x_agent_phone_old', '=', list_content['last_agent_id'])], limit=1)
                        call_status = list_content['call_status']
                        if call_status == 'miss':
                            call_link = False
                            call_download = False
                        else:
                            call_link = list_content['path']
                            call_download = list_content['path_download']
                        arr_time_talk = list_content['talk_time'].split(':')
                        time_talk = int(arr_time_talk[0]) * 3600 + int(arr_time_talk[1]) * 60 + int(arr_time_talk[2])

                        arr_time_hold = list_content['hold_time'].split(':')
                        time_hold = int(arr_time_hold[0]) * 3600 + int(arr_time_hold[1]) * 60 + int(arr_time_hold[2])
                        arr_time_wait = list_content['wait_time'].split(':')
                        time_wait = int(arr_time_wait[0]) * 3600 + int(arr_time_wait[1]) * 60 + int(arr_time_wait[2])
                        people_end = list_content['end_status']

                        self.env['phonecall'].create({
                            'name': name,
                            'call_type': call_type,
                            'call_date': time_start,
                            'phone': list_content['caller'],
                            'branch_hotline': list_content['called'],
                            'agent_text': list_content['last_agent_id'],
                            'many_agent_text': list_content['agent_id'],
                            'user_id': user_last_id and user_last_id.id or False,
                            'user_ids': user_ids and [(6,0, user_ids.ids)] or [],
                            'call_status': call_status,
                            'path_download': call_download,
                            'path': call_link,
                            'voip_phonecall_config_id': phone_config.id,
                            'hotline': phone_switchboard,
                            'hold_time': time_hold,
                            'wait_time': time_wait,
                            'talk_time': time_talk,
                            'end_time': (datetime.strptime(list_content['end_time'], "%Y-%m-%d %H:%M:%S") - timedelta(
                        hours=7)).strftime("%Y-%m-%d %H:%M:%S"),
                            'start_time': time_start,
                            'end_status': people_end,
                            'customer_3c_id': list_content['customer_id'],
                            'mobifone_id': list_content['id'],
                        })
                        dem_1 += 1
                    #todo lưu lại ngày cuối cùng được lấy ra trong lần lặp này
                    if count == len(contents):
                        page += 1
                dem += dem_1
            #todo cập nhật lại ngày bắt đầu và ngày kết thúc đồng bộ cho từng tổng đài
            if dem > 0:
                phone_config.date_start_synchronize = time_start
                phone_config.date_end_synchronize = False

    @api.model
    def partner_synchronize(self):
        Phonecall_Obj = self.env['phonecall'].sudo()
        Partner_Obj = self.env['res.partner'].sudo()
        User_Obj = self.env['res.users'].sudo()
        for phonecall_id in Phonecall_Obj.filtered(lambda phone: not phone.partner_id):
            partner_id = Partner_Obj.search([('phone', '=', str(phonecall_id.phone))], limit=1)
            if partner_id:
                phonecall_id.partner_id = partner_id.id
                if not partner_id.x_call_last_date or partner_id.x_call_last_date < phonecall_id.start_time:
                    partner_id.x_call_last_date = phonecall_id.start_time



    @api.constrains('phone')
    def _compute_partner(self):
        for phonecall in self:
            if phonecall.phone:
                partner_id = self.env['res.partner'].search([('phone', '=', str(phonecall.phone))], limit=1)
                if partner_id:
                    phonecall.partner_id = partner_id.id
                    if not partner_id.x_call_last_date or partner_id.x_call_last_date < phonecall.start_time:
                        partner_id.x_call_last_date = phonecall.start_time

    def action_listen(self):
        phonecall = self.env['phonecall'].search([('id', '=', self._context.get('phonecall_id'))])
        return {
            "type": "ir.actions.act_url",
            'name': 'Listen Path',
            'target': 'new',
            'url': phonecall.path,
        }

    def action_download(self):
        phonecall = self.env['phonecall'].search([('id', '=', self._context.get('phonecall_id'))])
        return {
            "type": "ir.actions.act_url",
            'name': 'Download Path',
            'target': 'self',
            'url': phonecall.path_download,
        }

# class SpiderScrapy(scrapy.Spider):
#     name = 'trading.view'
#
#     start_url = ['https://vn.tradingview.com/chart/OGPGCa8S/']


