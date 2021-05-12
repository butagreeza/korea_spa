from odoo import api, fields, models, _
from odoo.exceptions import except_orm, UserError


class IziCrmLead(models.Model):
    _inherit = 'crm.stage'

    @api.model_cr
    def init(self):
        if not self.env['crm.stage'].search([('x_code', '=', 'meeting')], limit=1):
            self.env['crm.stage'].create({
                'name': _('Meeting'),
                'x_code': 'meeting',
                'probability': 0
            })