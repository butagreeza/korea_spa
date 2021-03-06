# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm, UserError
from datetime import datetime, timedelta


class IziServiceCardUsingLine(models.Model):
    _inherit = 'izi.service.card.using.line'

    # def _domain_bed(self):
    #     ids = []
    #     branch_id = self.using_id.pos_session_id.config_id.pos_branch_id
    #     room_service_obj = self.env['pos.service.room'].search(
    #         [('branch_id', '=', branch_id.id), ('active', '=', True)])
    #     for line in room_service_obj:
    #         bed_service_obj = self.env['pos.service.bed'].search(
    #             [('room_id', '=', line.id), ('active', '=', True), ('state', '=', 'ready')])
    #         for id in bed_service_obj:
    #             ids.append(id.id)
    #     return [('id', 'in', ids)]

    bed_ids = fields.Many2many('pos.service.bed', string="Bed")
    state = fields.Selection([('new', "New"), ('working', "Working"), ('done', "Done")], default='new')
    partner_id = fields.Many2one('res.partner', related='using_id.customer_id', string='Partner', readonly=True)

    # @api.onchange('quantity', 'service_id')
    # def onchange_bed(self):
    #     ids = []
    #     branch_id = self.branch_id
    #     room_service_obj = self.env['pos.service.room'].search([('branch_id', '=', branch_id.id), ('active', '=', True)])
    #     for line in room_service_obj:
    #         bed_service_obj = self.env['pos.service.bed'].search([('room_id', '=', line.id), ('active', '=', True), ('state', '=', 'ready')])
    #         for id in bed_service_obj:
    #             ids.append(id.id)
    #     return {
    #         'domain': {
    #             'bed_ids': [('id', 'in', ids)]
    #         }
    #     }

    # @api.onchange('bed_ids')
    # def onchange_bed_bundle(self):
    #     for bed in self.bed_ids:
    #         if bed.branch_id != self.branch_id:
    #             self.bed_ids = False
    #     ids = []
    #     branch_id = self.branch_id
    #     room_service_obj = self.env['pos.service.room'].search(
    #         [('branch_id', '=', branch_id.id), ('active', '=', True)])
    #     for line in room_service_obj:
    #         bed_service_obj = self.env['pos.service.bed'].search(
    #             [('room_id', '=', line.id), ('active', '=', True), ('state', '=', 'ready')])
    #         for id in bed_service_obj:
    #             ids.append(id.id)
    #     return {
    #         'domain': {
    #             'bed_ids': [('id', 'in', ids)]
    #         }
    #     }

    @api.multi
    def action_choose_bed(self):
        view_id = self.env.ref('izi_manage_room.izi_service_card_choose_bed_view').id
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'name': 'Choose bed',
            'res_id': self.id,
            'res_model': 'izi.service.card.using.line',
            'views' : [(view_id, 'form')],
            'target': 'new',
            'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}}
        }

    @api.multi
    def action_confirm_bed(self):
        if self.state != 'new':
            raise except_orm("Th??ng b??o!", ("Tr???ng th??i ???? thay ?????i vui l??ng load l???i"))
        self.write({
            'state': 'working'
        })
        employee_ids = []
        doctor_ids = []
        for line in self.employee_ids:
            employee_ids.append(line.id)
        for line in self.doctor_ids:
            doctor_ids.append(line.id)
        if not self.bed_ids:
            raise UserError('B???n ch??a ch???n gi?????ng cho d???ch v??? %s.Vui l??ng ki???m tra l???i.' % str(self.service_id.name))
        for line in self.bed_ids:
            if line.state == 'busy':
                raise except_orm('C???nh b??o', ('Gi?????ng b???n ch???n ???? ???????c s??? d???ng.Vui l??ng ki???m tra l???i.'))
            line.date_start = datetime.now()
            date1 = datetime.strptime(line.date_start, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
            line.write({
                'state': 'busy',
                'employee_ids': [(4, k) for k in employee_ids],
                'doctor_ids': [(4, i) for i in doctor_ids],
                'hour': date1.hour,
                'minutes': date1.minute,
                'seconds': date1.second,
            })

    @api.multi
    def action_back(self):
        employee_ids = []
        doctor_ids = []
        for line in self.employee_ids:
            employee_ids.append(line.id)
        for line in self.doctor_ids:
            doctor_ids.append(line.id)

        if not self.state:
            self.state = 'working'
            for line in self.bed_ids:
                line.state = 'ready'
                line.employee_ids = None
                line.doctor_ids = None
        if self.sudo().using_id.state == 'done':
            raise except_orm("Th??ng b??o!", ("????n s??? d???ng ???? ????ng b???n kh??ng th??? thay d???i tr???ng th??i"))
        if self.state not in('working', 'done'):
            raise except_orm("Th??ng b??o!", ("Tr???ng th??i ???? thay ?????i vui l??ng load l???i"))
        if self.state == 'working':
            self.state = 'new'
            for line in self.bed_ids:
                line.state = 'ready'
                line.employee_ids = None
                line.doctor_ids = None
        if self.state == 'done':
            self.state = 'working'
            for line in self.bed_ids:
                if line.state == 'busy':
                    raise except_orm('C???nh b??o!', ('Gi?????ng b???n ch???n hi???n ??ang b???n.Vui l??ng ki???m tra l???i.'))
                line.write({
                    'state': 'busy',
                    'employee_ids': [(4, k) for k in employee_ids],
                    'doctor_ids': [(4, i) for i in doctor_ids],
                })

    @api.multi
    def action_choose_doctor(self):
        view_id = self.env.ref('izi_manage_room.izi_service_card_choose_doctor_view').id
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'name': 'Choose doctor',
            'res_id': self.id,
            'res_model': 'izi.service.card.using.line',
            'views': [(view_id, 'form')],
            'target': 'new',
            'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}}
        }

    @api.multi
    def action_done(self):
        if self.state != 'working':
            raise except_orm("Th??ng b??o!", ("Tr???ng th??i ???? thay ?????i vui l??ng load l???i"))
        if self.service_id.x_use_doctor and not self.doctor_ids:
            raise except_orm('Th??ng b??o', 'D???ch v??? [%s]%s ph???i ch???n b??c s??!' % (str(self.service_id.default_code), str(self.service_id.name)))
        self.write({
          'state': 'done'
        })
        for line in self.bed_ids:
            line.write({
                'state': 'ready',
            })
            line.employee_ids = None
            line.doctor_ids = None
            line.hour = None
            line.minutes = None
            line.seconds = None
        # self.bed_id.state = 'ready'


class IziServiceCardUsing(models.Model):
    _inherit = 'izi.service.card.using'

    @api.multi
    def action_done(self):
        res = super(IziServiceCardUsing, self).action_done()
        for line in self.service_card_ids:
            if line.state == 'new':
                line.action_confirm_bed()
            if line.state == 'working':
                line.action_done()
            if line.state != 'done':
                raise except_orm("C???nh b??o!", ("Vui l??ng c???p nh???t tr???ng th??i gi?????ng c???a d???ch v??? %s tr?????c khi ????ng ????n s??? d???ng" % (str(line.service_id.name))))
        for line in self.service_card1_ids:
            if line.state == 'new':
                line.action_confirm_bed()
            if line.state == 'working':
                line.action_done()
            if line.state != 'done':
                raise except_orm("C???nh b??o!", ("Vui l??ng c???p nh???t tr???ng th??i gi?????ng tr?????c khi ????ng ????n s??? d???ng"))

    @api.multi
    def action_cancel(self):
        for line in self.service_card_ids:
            line.state = 'done'
            for tmp in line.bed_ids:
                tmp.state = 'ready'
        for line in self.service_card1_ids:
            line.state = 'done'
            for tmp in line.bed_ids:
                tmp.state = 'ready'
        return super(IziServiceCardUsing, self).action_cancel()