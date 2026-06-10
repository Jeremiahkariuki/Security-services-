from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class SecurityAttendance(models.Model):
    _name = 'security.attendance'
    _description = 'Guard Attendance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'clock_in desc'

    name = fields.Char(
        string='Reference',
        compute='_compute_name',
        store=True
    )
    guard_id = fields.Many2one(
        'security.guard',
        string='Guard',
        required=True,
        tracking=True
    )
    shift_id = fields.Many2one(
        'security.shift',
        string='Shift',
        tracking=True
    )
    site_id = fields.Many2one(
        'security.site',
        string='Site',
        required=True,
        tracking=True
    )
    clock_in = fields.Datetime(
        string='Clock In',
        tracking=True
    )
    clock_out = fields.Datetime(
        string='Clock Out',
        tracking=True
    )
    hours_worked = fields.Float(
        string='Hours Worked',
        compute='_compute_hours_worked',
        store=True
    )
    late_checkin = fields.Boolean(
        string='Late Check-in',
        compute='_compute_late',
        store=True
    )
    date = fields.Date(
        string='Date',
        compute='_compute_date',
        store=True
    )
    state = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
    ], string='Status', default='present', tracking=True)

    gps_checkin_lat = fields.Float(string='Check-in Latitude', digits=(10, 7))
    gps_checkin_lng = fields.Float(string='Check-in Longitude', digits=(10, 7))
    gps_checkout_lat = fields.Float(string='Check-out Latitude', digits=(10, 7))
    gps_checkout_lng = fields.Float(string='Check-out Longitude', digits=(10, 7))

    patrol_log_ids = fields.One2many(
        'security.patrol.log',
        'attendance_id',
        string='Patrol Logs'
    )
    patrol_count = fields.Integer(
        string='Patrol Rounds',
        compute='_compute_patrol_count'
    )
    notes = fields.Text(string='Notes')

    # ── Computed Fields ──────────────────────────────
    @api.depends('guard_id', 'date')
    def _compute_name(self):
        for rec in self:
            if rec.guard_id and rec.clock_in:
                rec.name = f"{rec.guard_id.name} - {rec.clock_in.date()}"
            else:
                rec.name = 'New Attendance'

    @api.depends('clock_in')
    def _compute_date(self):
        for rec in self:
            if rec.clock_in:
                rec.date = rec.clock_in.date()
            else:
                rec.date = False

    @api.depends('clock_in', 'clock_out')
    def _compute_hours_worked(self):
        for rec in self:
            if rec.clock_in and rec.clock_out:
                delta = rec.clock_out - rec.clock_in
                rec.hours_worked = delta.total_seconds() / 3600
            else:
                rec.hours_worked = 0.0

    @api.depends('clock_in', 'shift_id')
    def _compute_late(self):
        for rec in self:
            if rec.clock_in and rec.shift_id:
                scheduled_start = rec.shift_id.start_time
                actual_hour = rec.clock_in.hour + rec.clock_in.minute / 60
                rec.late_checkin = actual_hour > (scheduled_start + 0.25)
            else:
                rec.late_checkin = False

    def _compute_patrol_count(self):
        for rec in self:
            rec.patrol_count = len(rec.patrol_log_ids)

    # ── Action Buttons ────────────────────────────────
    def action_clock_in(self):
        self.write({
            'clock_in': fields.Datetime.now(),
            'state': 'present',
        })

    def action_clock_out(self):
        if not self.clock_in:
            raise ValidationError("Cannot clock out without clocking in first.")
        self.write({
            'clock_out': fields.Datetime.now(),
        })

    @api.constrains('clock_in', 'clock_out')
    def _check_clock_times(self):
        for rec in self:
            if rec.clock_in and rec.clock_out:
                if rec.clock_out < rec.clock_in:
                    raise ValidationError(
                        "Clock out time cannot be before clock in time."
                    )


class SecurityPatrolLog(models.Model):
    _name = 'security.patrol.log'
    _description = 'Guard Patrol Log'
    _rec_name = 'checkpoint_name'
    _order = 'patrol_time desc'

    attendance_id = fields.Many2one(
        'security.attendance',
        string='Attendance',
        required=True,
        ondelete='cascade'
    )
    guard_id = fields.Many2one(
        'security.guard',
        string='Guard',
        related='attendance_id.guard_id',
        store=True
    )
    site_id = fields.Many2one(
        'security.site',
        string='Site',
        related='attendance_id.site_id',
        store=True
    )
    checkpoint_name = fields.Char(
        string='Checkpoint',
        required=True
    )
    patrol_time = fields.Datetime(
        string='Patrol Time',
        default=fields.Datetime.now,
        required=True
    )
    gps_lat = fields.Float(string='Latitude', digits=(10, 7))
    gps_lng = fields.Float(string='Longitude', digits=(10, 7))
    notes = fields.Text(string='Observations')
    incident_found = fields.Boolean(string='Incident Found')
