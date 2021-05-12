from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError


class RptCrmCustomerNew(models.TransientModel):
    _name = 'rpt.crm.customer.new'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    x_pos_config = fields.Many2many('pos.config', string="Pos Config")
    select_all = fields.Boolean('All Pos Config')

    @api.multi
    def create_report_crm_customer_new(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_crm_lead_new.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str3 = "&x_pos_config="
        if (self.select_all == True):
            list_id = ''
            pos_config = self.env['pos.config'].search([])
            for pos_config_id in pos_config:
                list_id += ',' + str(pos_config_id.id)
            param_str3 += (list_id[1:])
        else:
            list_id = ''
            for loc_id in self.x_pos_config:
                list_id += ',' + str(loc_id.id)
            param_str3 += (list_id[1:])
        param_str = param_str1 + param_str3
        # return {
        #     'type': 'ir.actions.act_url',
        #     'url': url + "/report/frameset?__report=report_korea/" + report_name + param_str,
        #     'target': 'new',
        # }
        return {
            "type": "ir.actions.client",
            'name': 'Báo cáo',
            'tag': 'BirtViewerAction',
            'target': 'new',
            'context': {'birt_link': url + "/report/frameset?__report=report_korea/" + report_name + param_str}
        }
