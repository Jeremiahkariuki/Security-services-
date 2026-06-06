from odoo import models, fields


class SecurityClient(models.Model):
    _name = 'security.client'
    _description = 'Security Client'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Company Name', required=True, tracking=True)
    contact_person = fields.Char(string='Contact Person')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    address = fields.Text(string='Address')
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string='Status', default='active', tracking=True)

    site_ids = fields.One2many(
        'security.site', 'client_id', string='Sites'
    )
    site_count = fields.Integer(
        string='Number of Sites',
        compute='_compute_site_count'
    )

    def _compute_site_count(self):
        for rec in self:
            rec.site_count = len(rec.site_ids)