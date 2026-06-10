from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class SecurityShift(models.Model):
    _name = 'security.shift'
    _description = 'Security Guard Shift'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'date desc, shift_type'

    name = fields.Char(
        string='Shift Reference',
        compute='_compute_name',
        store=True
    )
    roster_id = fields.Many2one(
        'security.roster',
        string='Roster',
        ondelete='cascade'
    )
    guard_id = fields.Many2one(
        'security.guard',
        string='Guard',
        required=True,
        tracking=True,
        domain=[('status', '=', 'active')]
    )
    site_id = fields.Many2one(
        'security.site',
        string='Site',
        required=True,
        tracking=True
    )
    supervisor_id = fields.Many2one(
        'security.guard',
        string='Supervisor',
        tracking=True
    )
    replacement_id = fields.Many2one(
        'security.guard',
        string='Replacement Guard',
        tracking=True
    )
    date = fields.Date(
        string='Shift Date',
        required=True,
        tracking=True,
        default=fields.Date.today
    )
    shift_type = fields.Selection([
        ('day', 'Day Shift (6AM - 6PM)'),
        ('night', 'Night Shift (6PM - 6AM)'),
        ('custom', 'Custom Hours'),
    ], string='Shift Type', required=True,
       default='day', tracking=True)

    start_time = fields.Float(string='Start Time', default=6.0)
    end_time = fields.Float(string='End Time', default=18.0)
    hours_worked = fields.Float(
        string='Hours Worked',
        compute='_compute_hours',
        store=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('ongoing', 'Ongoing'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    checked_in = fields.Datetime(string='Clock In', tracking=True)
    checked_out = fields.Datetime(string='Clock Out', tracking=True)
    notes = fields.Text(string='Notes')

    @api.depends('guard_id', 'site_id', 'date', 'shift_type')
    def _compute_name(self):
        for rec in self:
            if rec.guard_id and rec.date:
                shift = dict(self._fields['shift_type'].selection).get(
                    rec.shift_type, ''
                )
                rec.name = f"{rec.guard_id.name} - {shift} - {rec.date}"
            else:
                rec.name = 'New Shift'

    @api.depends('start_time', 'end_time', 'shift_type')
    def _compute_hours(self):
        for rec in self:
            if rec.shift_type == 'night':
                rec.hours_worked = 12.0
            elif rec.start_time and rec.end_time:
                if rec.end_time > rec.start_time:
                    rec.hours_worked = rec.end_time - rec.start_time
                else:
                    rec.hours_worked = 12.0
            else:
                rec.hours_worked = 0.0

    @api.constrains('guard_id', 'date', 'shift_type')
    def _check_double_booking(self):
        for rec in self:
            duplicate = self.search([
                ('guard_id', '=', rec.guard_id.id),
                ('date', '=', rec.date),
                ('shift_type', '=', rec.shift_type),
                ('state', '!=', 'cancelled'),
                ('id', '!=', rec.id),
            ])
            if duplicate:
                raise ValidationError(
                    f"{rec.guard_id.name} is already assigned "
                    f"to a {rec.shift_type} shift on {rec.date}."
                )

    def action_confirm(self):
        self.state = 'confirmed'

    def action_start(self):
        self.write({
            'state': 'ongoing',
            'checked_in': fields.Datetime.now(),
        })

    def action_done(self):
        self.write({
            'state': 'done',
            'checked_out': fields.Datetime.now(),
        })

    def action_cancel(self):
        self.state = 'cancelled'

    def action_reset(self):
        self.state = 'draft'


class SecurityRoster(models.Model):
    _name = 'security.roster'
    _description = 'Weekly Guard Roster'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(
        string='Roster Name',
        required=True,
        tracking=True
    )
    site_id = fields.Many2one(
        'security.site',
        string='Site',
        required=True,
        tracking=True
    )
    week_start = fields.Date(
        string='Week Start',
        required=True,
        tracking=True
    )
    week_end = fields.Date(
        string='Week End',
        compute='_compute_week_end',
        store=True
    )
    manager_id = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        tracking=True
    )
    shift_ids = fields.One2many(
        'security.shift',
        'roster_id',
        string='Shifts'
    )
    shift_count = fields.Integer(
        string='Total Shifts',
        compute='_compute_shift_count'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published'),
    ], string='Status', default='draft', tracking=True)
    notes = fields.Text(string='Notes')

    @api.depends('week_start')
    def _compute_week_end(self):
        for rec in self:
            if rec.week_start:
                rec.week_end = rec.week_start + timedelta(days=6)
            else:
                rec.week_end = False

    def _compute_shift_count(self):
        for rec in self:
            rec.shift_count = len(rec.shift_ids)

    def action_publish(self):
        self.state = 'published'
        for shift in self.shift_ids:
            shift.action_confirm()
