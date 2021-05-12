from odoo import api, fields, models, _
from odoo.exceptions import except_orm, UserError


class IziCrmLead(models.Model):
    _inherit = 'crm.stage'

    x_code = fields.Char(string='Code')

    _sql_constraints = {
        ('unique_x_code', 'unique(x_code)', ' Mã phải là duy nhất!')
    }