from odoo import models, fields


class SecuritySite(models.Model):
    _name = 'security.site'
    _description = 'Security Site'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Site Name', required=True, tracking=True)
    client_id = fields.Many2one(
        'security.client',
        string='Client',
        required=True,
        tracking=True
    )
    location = fields.Char(string='Location / Address')
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string='Risk Level', default='medium', tracking=True)

    required_guards = fields.Integer(
        string='Required Guards', default=1
    )
    contract_start = fields.Date(string='Contract Start')
    contract_end = fields.Date(string='Contract End')
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string='Status', default='active', tracking=True)

    guard_ids = fields.One2many(
        'security.guard', 'site_id', string='Assigned Guards'
    )
    guard_count = fields.Integer(
        string='Guards Deployed',
        compute='_compute_guard_count'
    )
    notes = fields.Text(string='Notes')

    def _compute_guard_count(self):
        for rec in self:
            rec.guard_count = len(
                rec.guard_ids.filtered(lambda g: g.status == 'active')
            )