# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError, UserError


class InheritCashManagement(models.Model):
    _inherit = 'account.cash'

    x_user_id = fields.Many2many('hr.employee', string='Beneficiary')
    revenue_id = fields.Many2one('pos.revenue.allocation', string='Allocation revenue')

    @api.multi
    def action_carrying(self):
        res = super(InheritCashManagement, self).action_carrying()
        # KOREA yêu cầu không tạo đơn phân bổ doanh thu
        # if self.x_user_id:
        # if self.type == 'in':
        #     revenue_id = self._auto_allocation(self.amount_total - (self.amount_total/100*self.journal_id.card_swipe_fees))
        # else:
        #     revenue_id = self._auto_allocation(-self.amount_total - (self.amount_total/100*self.journal_id.card_swipe_fees))
        # self.revenue_id = revenue_id.id
        return res

    def _auto_allocation(self, amount):
        partner_id = False
        for line in self.lines:
            partner_id = line.partner_id
            break
        if amount != 0:
            Allocation = self.env['pos.revenue.allocation']
            AllocationLine = self.env['pos.revenue.allocation.line']
            vals = {
                'cash_management_id': self.id,
                # 'partner_name':self.partner_id.name,
                'partner_id': partner_id.id,
                'partner_code': self.partner_id.x_code,
                'amount_total': amount,
                'amount_allocated': amount,
                'amount_res': 0,
                'date': fields.Datetime.now(),
                'style_allocation': 'percent',
                'state': 'draft',
                'pos_session_id': self.session_id.id,
            }
            revenue_id = Allocation.create(vals)
            if self.type == 'out':
                revenue_id.type = 'cash_out'
            else:
                revenue_id.type = 'cash_in'
            count_nvtv = 0
            for item in self.x_user_id:
                if item.job_id.x_code == 'NVTV':
                    count_nvtv += 1
            count = len(self.x_user_id)
            if count == count_nvtv or count_nvtv == 0:
                if count_nvtv == 0:
                    note = 'Nhân viên thừa hưởng'
                else:
                    note = 'Nhân viên tư vấn'
                # KOREA yêu cầu vẫn tạo đơn phân bổ doanh thu nếu không chọn người hương doanh thu
                if self.x_user_id:
                    for item in self.x_user_id:
                        vals_line = {
                            'employee_id': item.id,
                            'amount': 0,
                            'amount_total': 0,
                            'percent': 0,
                            'cash_management_id': self.id,
                            'note': note,
                            'revenue_allocation_id': revenue_id.id,
                        }
                        AllocationLine.create(vals_line)
                else:
                    vals_line = {
                        'employee_id': False,
                        'amount': 0,
                        'amount_total': 0,
                        'percent': 0,
                        'cash_management_id': self.id,
                        'note': note,
                        'revenue_allocation_id': revenue_id.id,
                    }
                    AllocationLine.create(vals_line)
            else:
                # KOREA yêu cầu vẫn tạo đơn phân bổ doanh thu nếu không chọn người hương doanh thu
                if self.x_user_id:
                    for item in self.x_user_id:
                        if item.job_id.x_code == 'NVTV':
                            vals_line = {
                                'employee_id': item.id,
                                'amount': 0,
                                'amount_total': 0,
                                'percent': 0,
                                'cash_management_id': self.id,
                                'note': 'Nhân viên tư vấn',
                                'revenue_allocation_id': revenue_id.id,
                            }
                            AllocationLine.create(vals_line)
                        else:
                            vals_line = {
                                'employee_id': item.id,
                                'amount': 0,
                                'amount_total': 0,
                                'percent': 0,
                                'cash_management_id': self.id,
                                'note': 'Nhân viên thừa hưởng',
                                'revenue_allocation_id': revenue_id.id,
                            }
                            AllocationLine.create(vals_line)
                else:
                    vals_line = {
                        'employee_id': False,
                        'amount': 0,
                        'amount_total': 0,
                        'percent': 0,
                        'cash_management_id': self.id,
                        'note': '',
                        'revenue_allocation_id': revenue_id.id,
                    }
                    AllocationLine.create(vals_line)
        return revenue_id