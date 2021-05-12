# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ServiceCalenderReminderLine(models.Model):
    _name = 'crm.service.calender.reminder.line'

    name = fields.Char("Name")
    partner_id = fields.Many2one('res.partner', "Partner")
    phone = fields.Char("Phone")
    date = fields.Date("Date")
    product_id = fields.Many2one('product.product', "Service")
    note = fields.Char("Note")
    description = fields.Char("Description")
    service_calender_reminder_id = fields.Many2one('crm.service.calender.reminder', "Service Calender")
    type = fields.Selection([('service', "Service"), ('card', "Card")])
    total_quantity = fields.Float('Toal Quantity')
    quantity_used = fields.Float("Quantity Used")
    origin = fields.Char("Origin")
#     Sangla them ngay 28_11_2018
#     thêm ghi chú nếu khách hàng đến trước ngày nhắc lịch để thêm vào
    note_before_custom = fields.Char('Note Before Custom')
    employee_id = fields.Many2one('hr.employee', "Employee")
    user_id = fields.Many2one('res.users', related='partner_id.x_manage_user_id', string='User', store=True)
    survey_id = fields.Many2one('survey.survey', "Survey")
    survey_user_input_id = fields.Many2one('survey.user_input', "Survey User Input")

    @api.multi
    def action_start_survey(self):
        """ Open the website page with the survey form """
        self.ensure_one()
        # token = self.survey_id.env.context.get('survey_token')
        # trail = "/%s" % token if token else ""
        user_input = self.env['survey.user_input'].sudo().create(
            {'survey_id': self.survey_id.id, 'test_entry': False, 'type': 'manually'})
        token = user_input.token
        self.survey_user_input_id = user_input.id
        # return {
        #     'type': 'ir.actions.act_url',
        #     'name': "Start Survey",
        #     'target': 'new',
        #     'url': self.survey_id.with_context(relative_url=True).public_url +'/'+ token
        # }

        return {
            "type": "ir.actions.client",
            'name': 'Start Survey',
            'tag': 'BirtViewerAction',
            'target': 'new',
            'context': {'birt_link': self.survey_id.with_context(relative_url=True).public_url +'/'+ token}
        }