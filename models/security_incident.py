from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SecurityIncident(models.Model):
    _name = 'security.incident'
    _description = 'Security Incident Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'date_reported desc'

    name = fields.Char(
        string='Incident Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )
    site_id = fields.Many2one(
        'security.site',
        string='Site',
        required=True,
        tracking=True
    )
    shift_id = fields.Many2one(
        'security.shift',
        string='Shift',
        tracking=True
    )
    reported_by = fields.Many2one(
        'security.guard',
        string='Reported By',
        required=True,
        tracking=True
    )
    assigned_to = fields.Many2one(
        'res.users',
        string='Assigned To',
        tracking=True
    )
    incident_type = fields.Selection([
        ('theft', 'Theft'),
        ('vandalism', 'Vandalism'),
        ('trespassing', 'Trespassing'),
        ('assault', 'Assault'),
        ('fire', 'Fire'),
        ('medical', 'Medical Emergency'),
        ('suspicious', 'Suspicious Activity'),
        ('access', 'Unauthorized Access'),
        ('other', 'Other'),
    ], string='Incident Type', required=True, tracking=True)

    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string='Severity', required=True,
       default='medium', tracking=True)

    date_reported = fields.Datetime(
        string='Date Reported',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )
    date_occurred = fields.Datetime(
        string='Date Occurred',
        required=True,
        tracking=True
    )
    description = fields.Text(
        string='Description',
        required=True
    )
    action_taken = fields.Text(
        string='Immediate Action Taken'
    )
    resolution = fields.Text(
        string='Resolution / Follow Up'
    )
    state = fields.Selection([
        ('new', 'New'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('escalated', 'Escalated'),
    ], string='Status', default='new', tracking=True)

    photo_ids = fields.Many2many(
        'ir.attachment',
        'incident_attachment_rel',
        'incident_id',
        'attachment_id',
        string='Photos / Evidence'
    )
    photo_count = fields.Integer(
        string='Photos',
        compute='_compute_photo_count'
    )
    police_report = fields.Boolean(
        string='Police Report Filed',
        tracking=True
    )
    police_report_no = fields.Char(
        string='Police Report Number'
    )
    injuries = fields.Boolean(
        string='Injuries Involved',
        tracking=True
    )
    property_damage = fields.Boolean(
        string='Property Damage',
        tracking=True
    )
    estimated_loss = fields.Float(
        string='Estimated Loss (KES)',
        tracking=True
    )

    def _compute_photo_count(self):
        for rec in self:
            rec.photo_count = len(rec.photo_ids)

    # ── Sequence ──────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'security.incident'
                ) or 'INC/0001'
        return super().create(vals_list)

    # ── Action Buttons ────────────────────────────────
    def action_review(self):
        self.state = 'under_review'

    def action_resolve(self):
        if not self.resolution:
            raise ValidationError(
                "Please enter a resolution before closing."
            )
        self.state = 'resolved'

    def action_close(self):
        self.state = 'closed'

    def action_escalate(self):
        self.state = 'escalated'
        self.message_post(
            body=f"Incident escalated by {self.env.user.name}. "
                 f"Severity: {self.severity}",
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )

    def action_reopen(self):
        self.state = 'new'

    # ── Severity Color ────────────────────────────────
    def _get_severity_color(self):
        colors = {
            'low': 10,
            'medium': 3,
            'high': 2,
            'critical': 1,
        }
        return colors.get(self.severity, 0)
