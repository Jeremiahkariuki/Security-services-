from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SecurityComplaint(models.Model):
    _name = 'security.complaint'
    _description = 'Guard Complaint'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'date_raised desc'

    name = fields.Char(
        string='Complaint Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )
    guard_id = fields.Many2one(
        'security.guard',
        string='Guard',
        required=True,
        tracking=True
    )
    subject = fields.Char(
        string='Subject',
        required=True,
        tracking=True
    )
    description = fields.Text(
        string='Description',
        required=True
    )
    date_raised = fields.Datetime(
        string='Date Raised',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )
    complaint_type = fields.Selection([
        ('salary', 'Salary Issue'),
        ('harassment', 'Harassment'),
        ('working_conditions', 'Working Conditions'),
        ('equipment', 'Equipment Issue'),
        ('schedule', 'Schedule Issue'),
        ('management', 'Management Issue'),
        ('other', 'Other'),
    ], string='Complaint Type', required=True, tracking=True)

    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Priority', default='medium', tracking=True)

    state = fields.Selection([
        ('new', 'New'),
        ('in_review', 'In Review'),
        ('resolved', 'Resolved'),
        ('escalated', 'Escalated to CEO'),
        ('closed', 'Closed'),
        ('referred', 'Referred Back'),
    ], string='Status', default='new', tracking=True)

    # Resolution fields
    reviewed_by = fields.Many2one(
        'res.users',
        string='Reviewed By',
        tracking=True
    )
    resolution_notes = fields.Text(
        string='Resolution Notes',
        tracking=True
    )
    date_resolved = fields.Datetime(
        string='Date Resolved',
        tracking=True
    )

    # Escalation fields
    escalated_by = fields.Many2one(
        'res.users',
        string='Escalated By',
        tracking=True
    )
    date_escalated = fields.Datetime(
        string='Date Escalated',
        tracking=True
    )
    ceo_notes = fields.Text(
        string='CEO Notes',
        tracking=True
    )
    ceo_notified = fields.Boolean(
        string='CEO Notified',
        default=False
    )

    # ── Sequence ──────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'security.complaint'
                ) or 'CMP/0001'
        return super().create(vals_list)

    # ── Action Buttons ────────────────────────────────
    def action_review(self):
        self.write({
            'state': 'in_review',
            'reviewed_by': self.env.user.id,
        })

    def action_resolve(self):
        if not self.resolution_notes:
            raise ValidationError(
                "Please enter resolution notes before resolving."
            )
        self.write({
            'state': 'resolved',
            'date_resolved': fields.Datetime.now(),
            'reviewed_by': self.env.user.id,
        })
        self.message_post(
            body=f"Complaint resolved by {self.env.user.name}. "
                 f"Resolution: {self.resolution_notes}",
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )

    def action_escalate_to_ceo(self):
        self.write({
            'state': 'escalated',
            'escalated_by': self.env.user.id,
            'date_escalated': fields.Datetime.now(),
            'ceo_notified': True,
        })
        # Send notification to CEO group
        ceo_group = self.env.ref(
            'security_services.group_security_ceo'
        )
        for user in ceo_group.users:
            self.env['bus.bus']._sendone(
                user.partner_id,
                'simple_notification',
                {
                    'title': 'New Complaint Escalated',
                    'message': f'Complaint {self.name} from '
                               f'{self.guard_id.name} requires your attention.',
                    'type': 'warning',
                    'sticky': True,
                }
            )
        self.message_post(
            body=f"Complaint escalated to CEO by {self.env.user.name}.",
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )

    def action_close(self):
        self.write({
            'state': 'closed',
            'date_resolved': fields.Datetime.now(),
        })

    def action_refer_back(self):
        if not self.ceo_notes:
            raise ValidationError(
                "Please add CEO notes before referring back."
            )
        self.write({'state': 'referred'})
        self.message_post(
            body=f"Referred back by CEO with notes: {self.ceo_notes}",
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )

    def action_reopen(self):
        self.write({'state': 'in_review'})
