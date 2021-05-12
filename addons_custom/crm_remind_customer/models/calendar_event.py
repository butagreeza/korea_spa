
from odoo import models, fields,api, _


class CalenderEvent(models.Model):
    _inherit = 'calendar.event'

    x_crm_remind_customer_id = fields.Many2one('crm.service.calender.reminder', "Crm Remind Customer")
