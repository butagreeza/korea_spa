# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
import logging
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class JobRevenueMonthly(models.Model):
    _name = 'res.partner.revenue.monthly'

    name = fields.Char(string='Name')
    type = fields.Selection([('six_month', "Six Month"), ('one_year', "One Year"), ('two_year', "Two Year")])
    # date = fields.Date(string="Date")
    lines = fields.One2many('res.partner.revenue.monthly.line', 'partner_revenue_monthly', string='List Customer')
    x_config_id = fields.Many2one('pos.config', string='Pos Config')

    def job_revenue_moth(self):
        a = 'HN%'
        b = 'SG%'
        obj_revenue_monthly = self.env['res.partner.revenue.monthly']
        obj_revenue_monthly_line = self.env['res.partner.revenue.monthly.line']
        partner_revenue_monthly_hn_1 = obj_revenue_monthly.search([('type', '=', 'six_month'), ('x_config_id', '=', 1)])
        if partner_revenue_monthly_hn_1.id == False:
            partner_revenue_monthly_hn_1 = obj_revenue_monthly.create({
                'name': 'DSKH Hà Nội chưa phát sinh doanh thu trong 6 tháng',
                'type': 'six_month',
                'x_config_id': 1
            })
        partner_revenue_monthly_hn_2 = obj_revenue_monthly.search([('type', '=', 'one_year'), ('x_config_id', '=', 1)])
        if partner_revenue_monthly_hn_2.id == False:
            partner_revenue_monthly_hn_2 = obj_revenue_monthly.create({
                'name': 'DSKH Hà Nội chưa phát sinh doanh thu  trong 1 năm',
                'type': 'one_year',
                'x_config_id': 1
            })
        partner_revenue_monthly_hn_3 = obj_revenue_monthly.search([('type', '=', 'two_year'), ('x_config_id', '=', 1)])
        if partner_revenue_monthly_hn_3.id == False:
            partner_revenue_monthly_hn_3 = obj_revenue_monthly.create({
                'name': 'DSKH Hà Nội chưa phát sinh doanh thu  trong 2 năm',
                'type': 'two_year',
                'x_config_id': 1
            })
        partner_revenue_monthly_sg_1 = obj_revenue_monthly.search([('type', '=', 'six_month'), ('x_config_id', '=', 2)])
        if partner_revenue_monthly_sg_1.id == False:
            partner_revenue_monthly_sg_1 = obj_revenue_monthly.create({
                'name': 'DSKH Sài Gòn chưa phát sinh doanh thu trong 6 tháng',
                'type': 'six_month',
                'x_config_id': 2
            })
        partner_revenue_monthly_sg_2 = obj_revenue_monthly.search([('type', '=', 'one_year'), ('x_config_id', '=', 2)])
        if partner_revenue_monthly_sg_2.id == False:
            partner_revenue_monthly_sg_2 = obj_revenue_monthly.create({
                'name': 'DSKH Sài Gòn chưa phát sinh doanh thu trong 1 năm',
                'type': 'one_year',
                'x_config_id': 2
            })
        partner_revenue_monthly_sg_3 = obj_revenue_monthly.search([('type', '=', 'two_year'), ('x_config_id', '=', 2)])
        if partner_revenue_monthly_sg_3.id == False:
            partner_revenue_monthly_sg_3 = obj_revenue_monthly.create({
                'name': 'DSKH Sài Gòn chưa phát sinh doanh thu trong 2 năm',
                'type': 'two_year',
                'x_config_id': 2
            })
        partner_two_year_hn = self.monthly_revenue(24, date.today(), 1, a)
        object_line_1 = obj_revenue_monthly_line.search(
            [('partner_revenue_monthly', '=', partner_revenue_monthly_hn_3.id)])
        for line_1 in object_line_1:
            line_1.unlink()
        if len(partner_two_year_hn) > 0:
            for line in partner_two_year_hn:
                if line['x_revenue_old'] is None or line['x_revenue_old'] is False:
                    line['x_revenue_old'] = 0.0
                if line['sum_revenue'] is None or line['sum_revenue'] is False:
                    line['sum_revenue']=0.0
                vals = {
                    'partner_revenue_monthly': partner_revenue_monthly_hn_3.id,
                    'revenue_old': line['x_revenue_old']  + line['sum_revenue'] ,
                    'partner_id': line['id'],
                    # 'revenue_monthly':partner_one_year_hn['revenue_old'],
                }
                obj_revenue_monthly_line.create(vals)
        partner_one_year_hn = self.monthly_revenue(12, date.today(), 1, a)
        object_line_2 = obj_revenue_monthly_line.search(
            [('partner_revenue_monthly', '=', partner_revenue_monthly_hn_2.id)])
        for line_2 in object_line_2:
            line_2.unlink()
        if len(partner_one_year_hn) > 0:
            for line in partner_one_year_hn:
                object_line = obj_revenue_monthly_line.search([('partner_id', '=', line['id'])])
                if len(object_line) <= 0:
                    if line['x_revenue_old'] is None or line['x_revenue_old'] is False:
                        line['x_revenue_old'] = 0.0
                    if line['sum_revenue'] is None or line['sum_revenue'] is False:
                        line['sum_revenue'] = 0.0
                    vals = {
                        'partner_revenue_monthly': partner_revenue_monthly_hn_2.id,
                        'revenue_old': line['x_revenue_old'] + line['sum_revenue'],
                        'partner_id': line['id'],
                        # 'revenue_monthly':partner_one_year_hn['revenue_old'],
                    }
                    obj_revenue_monthly_line.create(vals)
        partner_six_month_hn = self.monthly_revenue(6, date.today(), 1, a)
        object_line_3 = obj_revenue_monthly_line.search(
            [('partner_revenue_monthly', '=', partner_revenue_monthly_hn_1.id)])
        for line_3 in object_line_3:
            line_3.unlink()
        if len(partner_six_month_hn) > 0:
            for line in partner_six_month_hn:
                object_line = obj_revenue_monthly_line.search([('partner_id', '=', line['id'])])
                if len(object_line) <= 0:
                    if line['x_revenue_old'] is None or line['x_revenue_old'] is False:
                        line['x_revenue_old'] = 0.0
                    if line['sum_revenue'] is None or line['sum_revenue'] is False:
                        line['sum_revenue'] = 0.0
                    vals = {
                        'partner_revenue_monthly': partner_revenue_monthly_hn_1.id,
                        'revenue_old': line['x_revenue_old'] + line['sum_revenue'],
                        'partner_id': line['id'],
                        # 'revenue_monthly':partner_one_year_hn['revenue_old'],
                    }
                    obj_revenue_monthly_line.create(vals)
        partner_two_year_sg = self.monthly_revenue(24, date.today(), 2, b)
        object_line_4 = obj_revenue_monthly_line.search(
            [('partner_revenue_monthly', '=', partner_revenue_monthly_sg_3.id)])
        for line_4 in object_line_4:
            line_4.unlink()
        if len(partner_two_year_sg) > 0:
            for line in partner_two_year_sg:
                if line['x_revenue_old'] is None or line['x_revenue_old'] is False:
                    line['x_revenue_old'] = 0.0
                if line['sum_revenue'] is None or line['sum_revenue'] is False:
                    line['sum_revenue']=0.0
                vals = {
                    'partner_revenue_monthly': partner_revenue_monthly_sg_3.id,
                    'revenue_old': line['x_revenue_old']  + line['sum_revenue'] ,
                    'partner_id': line['id'],
                    # 'revenue_monthly':partner_one_year_hn['revenue_old'],
                }
                obj_revenue_monthly_line.create(vals)
        partner_one_year_sg = self.monthly_revenue(12, date.today(), 2, b)
        object_line_5 = obj_revenue_monthly_line.search(
            [('partner_revenue_monthly', '=', partner_revenue_monthly_sg_2.id)])
        for line_5 in object_line_5:
            line_5.unlink()
        if len(partner_one_year_sg) > 0:
            for line in partner_one_year_sg:
                object_line = obj_revenue_monthly_line.search([('partner_id', '=', line['id'])])
                if len(object_line) <= 0:
                    if line['x_revenue_old'] is None or line['x_revenue_old'] is False:
                        line['x_revenue_old'] = 0.0
                    if line['sum_revenue'] is None or line['sum_revenue'] is False:
                        line['sum_revenue'] = 0.0
                    vals = {
                        'partner_revenue_monthly': partner_revenue_monthly_sg_2.id,
                        'revenue_old': line['x_revenue_old'] + line['sum_revenue'],
                        'partner_id': line['id'],
                        # 'revenue_monthly':partner_one_year_hn['revenue_old'],
                    }
                    obj_revenue_monthly_line.create(vals)
        partner_six_month_sg = self.monthly_revenue(6, date.today(), 2, b)
        object_line_6 = obj_revenue_monthly_line.search(
            [('partner_revenue_monthly', '=', partner_revenue_monthly_sg_1.id)])
        for line_6 in object_line_6:
            line_6.unlink()
        if len(partner_six_month_sg) > 0:
            for line in partner_six_month_sg:
                object_line = obj_revenue_monthly_line.search([('partner_id', '=', line['id'])])
                if len(object_line) <= 0:
                    if line['x_revenue_old'] is None or line['x_revenue_old'] is False:
                        line['x_revenue_old'] = 0.0
                    if line['sum_revenue'] is None or line['sum_revenue'] is False:
                        line['sum_revenue'] = 0.0
                    vals = {
                        'partner_revenue_monthly': partner_revenue_monthly_sg_1.id,
                        'revenue_old': line['x_revenue_old'] + line['sum_revenue'],
                        'partner_id': line['id'],
                        # 'revenue_monthly':partner_one_year_hn['revenue_old'],
                    }
                    obj_revenue_monthly_line.create(vals)
        return True

    def monthly_revenue(self, monthly, to_date, x_pos_config, x_code):
        to_date = str(to_date)
        from_date = str(date.today() + relativedelta(months=-monthly))
        query_revenue = '''SELECT a.*,g.sum as sum_revenue
                            FROM res_partner a
                                    LEFT JOIN res_users c ON a.x_manage_user_id =  c.id
                                    LEFT JOIN (SELECT sum(amount),partner_id
                                                            FROM crm_vip_customer_revenue
                                                            WHERE date <= %s
                                                            GROUP BY partner_id) g ON g.partner_id =  a.id
                                    WHERE a.id not in (SELECT partner_id
                                                            FROM (SELECT sum(amount),partner_id
                                                                                FROM crm_vip_customer_revenue
                                                                                WHERE date <= %s and date >= %s
                                                                                GROUP BY partner_id ) b WHERE sum >0)
                                                and customer = 't' and (c.x_pos_config_id = %s or a.x_code LIKE %s)
                                        '''
        self.env.cr.execute(query_revenue, (from_date, to_date, from_date,
                                            x_pos_config, x_code))
        partners = self.env.cr.dictfetchall()
        return partners


class JobRevenueMonthlyLine(models.Model):
    _name = 'res.partner.revenue.monthly.line'

    partner_revenue_monthly = fields.Many2one('res.partner.revenue.monthly', string='Revenue Monthly')
    revenue_old = fields.Float(string='Revenue Old')
    partner_id = fields.Many2one('res.partner', string='Res Partner')
    # revenue_monthly = fields.Float(string="Monthly")
