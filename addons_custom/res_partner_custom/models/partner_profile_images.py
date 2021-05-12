# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.tools import float_compare, pycompat
from datetime import datetime
from odoo.exceptions import except_orm, ValidationError


class Partner(models.Model):
    _inherit = "res.partner"

    profile_image_ids = fields.One2many('partner.profile.image', 'partner_id', string='Profile image', copy=False)
    profile_image_count = fields.Integer(string='Profile images', compute='_compute_profile_image_ids')

    @api.multi
    def action_view_profile_image(self):

        action = self.env.ref('res_partner_custom.profile_image_action_window_by_partner').read()[0]
        profile_images = self.mapped('profile_image_ids')
        if len(profile_images) > 1:
            action['domain'] = [('id', 'in', profile_images.ids)]
            action['context'] = {'default_partner_id': self.id}
        elif profile_images:
            action['views'] = [(self.env.ref('res_partner_custom.partner_profile_image_form_view').id, 'form')]
            action['context'] = {'default_partner_id': self.id}
            action['res_id'] = profile_images.id
        else:
            action['domain'] = [('id', '=', 0)]
            action['context'] = {'default_partner_id': self.id}
        return action

    @api.depends('profile_image_count')
    def _compute_profile_image_ids(self):
        for line in self:
            line.profile_image_count = len(line.profile_image_ids)


class PartnerProfileImage(models.Model):
    _name = "partner.profile.image"

    name = fields.Char()
    partner_id = fields.Many2one('res.partner')
    note = fields.Text(string="Note")

    image_large = fields.Binary(
        "Large-sized Image", attachment=True)
    image_small = fields.Binary(
        "Small-sized image", compute='_compute_images')

    @api.one
    @api.depends('image_large')
    def _compute_images(self):
        if self._context.get('bin_size'):
            self.image_small = self.image_large
        else:
            resized_images = tools.image_get_resized_images(self.image_large, return_big=True, avoid_resize_medium=True)
            self.image_small = resized_images['image_small']