# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosServiceBed(models.Model):
    _name = 'pos.service.bed'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", track_visibility='onchange')
    code = fields.Char("Code", track_visibility='onchange', copy=False)
    room_id = fields.Many2one('pos.service.room', "Room",track_visibility='onchange')
    state = fields.Selection([('ready', "Ready"), ('busy', "Busy"), ('maintenance', "Maintenance")], default='ready')
    branch_id = fields.Many2one('res.branch', related="room_id.branch_id", string="Branch",track_visibility='onchange', store=True, readonly=True)
    active = fields.Boolean("Active",default=True, track_visibility='onchange')
    # time = fields.Float("Time")
    date_start = fields.Datetime("Data Start")
    hour = fields.Float("Hour")
    minutes = fields.Float("Minutes")
    seconds = fields.Float("Seconds")
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_employee_pos_service_bed',
                                    'employee_pos_service_bed_id', 'hr_employee_id', string='Employee')
    employee_name = fields.Char(string='Employee', compute='get_name_employee')
    doctor_ids = fields.Many2many('hr.employee', 'hr_employee_doctor_pos_serivce_bed',
                                  'doctor_pos_service_bed_id', 'hr_employee_id', string='Doctor')
    doctor_name = fields.Char(string='Doctor', compute='get_name_employee')

    @api.depends('employee_ids')
    def get_name_employee(self):
        for detail in self:
            if detail.employee_ids:
                employee_name = ''
                for emp in detail.employee_ids:
                    employee_name += emp.name + ','
                detail.employee_name = employee_name
            else:
                detail.doctor_name = None

            if detail.doctor_ids:
                doctor_name = ''
                for doctor in detail.doctor_ids:
                    doctor_name += doctor.name + ','
                detail.doctor_name = doctor_name
            else:
                detail.doctor_name = None

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Code is unique'),
    ]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = ['|', '|', ('name', operator, name), ('code', operator, name), ('room_id.name', operator, name)] + args
        res = self.search(args, limit=limit)
        return res.name_get()

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = '%s[%s:%s]' % (str(record.name), str(record.branch_id.code), str(record.room_id.name), )
            result.append((record.id, name))
        return result

    @api.multi
    def action_maintenace(self):
        self.state = 'maintenance'

    @api.multi
    def action_ready(self):
        self.state = 'ready'