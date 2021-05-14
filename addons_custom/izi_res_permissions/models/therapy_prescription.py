# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError, MissingError, except_orm
import logging
_logger = logging.getLogger(__name__)


class TherapyPrescription(models.Model):
    _inherit = 'therapy.prescription'

    @api.multi
    def write(self, values):
        res = super(TherapyPrescription, self).write(values)
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        _logger.error('id  ====== %s' % self.env.uid)
        if user_id.has_group('base.group_system') or user_id.has_group('izi_res_permissions.group_leader_accountant'):
            pass
        else:
            if self.s.state != 'opened':
                raise except_orm(("Cảnh báo!"), ('Phiên làm việc của PCĐ này đã đóng. Vui lòng liên hệ Admin để được giải quyết.'))
        return res