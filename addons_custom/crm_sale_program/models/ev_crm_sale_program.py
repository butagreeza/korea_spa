# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, RedirectWarning, except_orm
from datetime import date, datetime,timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import mute_logger
import logging
import time
import calendar



class crm_sale_program_history(models.Model):
    _name = 'crm.sale.program.history'

    program_id = fields.Many2one('crm.sale.program', string='Program')
    partner_id = fields.Many2one('res.partner', string='Partner')
    # period_id = fields.Many2one('account.period', string='Period')
    #
    def action_job_crm_sale_program_history(self):
        obj_sale_program = self.env['crm.sale.program']
        obj_sale_program_line = self.env['crm.sale.program.line']
        now = time.strftime('%Y-%m-%d')
        thang = now[5:7]
        month = time.strftime('%m')
        year = time.strftime('%Y')
        month_date = date(int(year),int(month), 1)

        date_from = month_date.replace(day=1)

        date_to = month_date.replace(day=calendar.monthrange(month_date.year, month_date.month)[1])

        # cập nhật khách hàng sắp sinh nhật vào chương trình kinh doanh
        query_birthday = '''SELECT id from res_partner WHERE extract(MONTH from x_birthday ) = %s 
                                and customer = TRUE 
                                AND active = True
                                AND supplier = FALSE
                                AND is_company = FALSE
                                AND employee = FALSE
                            '''
        self._cr.execute(query_birthday, (thang,))
        partners = self._cr.dictfetchall()

        if date_from and date_to:
            new_sale_program_birthday = obj_sale_program.create( {
                'name': 'Danh sách sinh nhật khách hàng  ' +month+'/'+year,
                'type': 'birthday',
                'from_date': date_from,
                'to_date': date_to,
                'description': 'sinh nhật khách hàng'
            })
            if new_sale_program_birthday:
                if len(partners) >= 1:
                    for partner in partners:
                        partner_id = partner['id']
                        object = self.env['res.partner'].search([('id','=',partner_id)])
                        if len(object) > 0:
                            rank = object.x_rank.id
                        else:
                            rank = False
                        new_sale_program_line = obj_sale_program_line.create({
                            'program_id': new_sale_program_birthday.id,
                            'partner_id': partner_id,
                        })
