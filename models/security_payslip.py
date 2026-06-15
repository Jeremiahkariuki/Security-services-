from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date
import calendar


class SecurityPayslip(models.Model):
    _name = 'security.payslip'
    _description = 'Guard Payslip'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'date_from desc'

    name = fields.Char(
        string='Payslip Reference',
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
    month = fields.Selection([
        ('1', 'January'), ('2', 'February'),
        ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'),
        ('11', 'November'), ('12', 'December'),
    ], string='Month', required=True, tracking=True)
    year = fields.Integer(
        string='Year',
        required=True,
        default=lambda self: date.today().year,
        tracking=True
    )
    date_from = fields.Date(
        string='From',
        compute='_compute_dates',
        store=True
    )
    date_to = fields.Date(
        string='To',
        compute='_compute_dates',
        store=True
    )

    # Earnings
    basic_salary = fields.Float(
        string='Basic Salary (KES)',
        tracking=True
    )
    house_allowance = fields.Float(
        string='House Allowance (KES)',
        tracking=True
    )
    transport_allowance = fields.Float(
        string='Transport Allowance (KES)',
        tracking=True
    )
    other_allowances = fields.Float(
        string='Other Allowances (KES)',
        tracking=True
    )
    gross_pay = fields.Float(
        string='Gross Pay (KES)',
        compute='_compute_gross',
        store=True
    )

    # Deductions
    nhif = fields.Float(
        string='NHIF (KES)',
        compute='_compute_deductions',
        store=True
    )
    nssf = fields.Float(
        string='NSSF (KES)',
        compute='_compute_deductions',
        store=True
    )
    paye = fields.Float(
        string='PAYE Tax (KES)',
        compute='_compute_deductions',
        store=True
    )
    other_deductions = fields.Float(
        string='Other Deductions (KES)',
        tracking=True
    )
    total_deductions = fields.Float(
        string='Total Deductions (KES)',
        compute='_compute_total_deductions',
        store=True
    )

    # Net Pay
    net_pay = fields.Float(
        string='Net Pay (KES)',
        compute='_compute_net_pay',
        store=True
    )

    # Attendance
    days_worked = fields.Integer(
        string='Days Worked',
        tracking=True
    )
    shifts_worked = fields.Integer(
        string='Shifts Worked',
        compute='_compute_shifts_worked',
        store=True
    )

    # Payment
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
    ], string='Status', default='draft', tracking=True)

    payment_date = fields.Date(
        string='Payment Date',
        tracking=True
    )
    payment_method = fields.Selection([
        ('bank', 'Bank Transfer'),
        ('mpesa', 'M-Pesa'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
    ], string='Payment Method', tracking=True)
    payment_reference = fields.Char(
        string='Payment Reference',
        tracking=True
    )
    paid_by = fields.Many2one(
        'res.users',
        string='Paid By',
        tracking=True
    )
    notes = fields.Text(string='Notes')

    # ── Sequence ──────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'security.payslip'
                ) or 'PAY/0001'
        return super().create(vals_list)

    # ── Computed Fields ──────────────────────────────
    @api.depends('month', 'year')
    def _compute_dates(self):
        for rec in self:
            if rec.month and rec.year:
                month = int(rec.month)
                year = int(rec.year)
                last_day = calendar.monthrange(year, month)[1]
                rec.date_from = date(year, month, 1)
                rec.date_to = date(year, month, last_day)
            else:
                rec.date_from = False
                rec.date_to = False

    @api.depends('basic_salary', 'house_allowance',
                 'transport_allowance', 'other_allowances')
    def _compute_gross(self):
        for rec in self:
            rec.gross_pay = (
                rec.basic_salary +
                rec.house_allowance +
                rec.transport_allowance +
                rec.other_allowances
            )

    @api.depends('gross_pay', 'basic_salary')
    def _compute_deductions(self):
        for rec in self:
            # NHIF calculation (Kenya 2024 rates)
            gross = rec.gross_pay
            if gross <= 5999:
                rec.nhif = 150
            elif gross <= 7999:
                rec.nhif = 300
            elif gross <= 11999:
                rec.nhif = 400
            elif gross <= 14999:
                rec.nhif = 500
            elif gross <= 19999:
                rec.nhif = 600
            elif gross <= 24999:
                rec.nhif = 750
            elif gross <= 29999:
                rec.nhif = 850
            elif gross <= 34999:
                rec.nhif = 900
            elif gross <= 39999:
                rec.nhif = 950
            elif gross <= 44999:
                rec.nhif = 1000
            elif gross <= 49999:
                rec.nhif = 1100
            elif gross <= 59999:
                rec.nhif = 1200
            elif gross <= 69999:
                rec.nhif = 1300
            elif gross <= 79999:
                rec.nhif = 1400
            elif gross <= 89999:
                rec.nhif = 1500
            elif gross <= 99999:
                rec.nhif = 1600
            else:
                rec.nhif = 1700

            # NSSF - 6% of basic salary (max 2160)
            rec.nssf = min(rec.basic_salary * 0.06, 2160)

            # PAYE (simplified Kenya tax bands 2024)
            taxable = gross - rec.nhif - rec.nssf
            if taxable <= 24000:
                rec.paye = taxable * 0.10
            elif taxable <= 32333:
                rec.paye = 2400 + (taxable - 24000) * 0.25
            elif taxable <= 500000:
                rec.paye = 4483 + (taxable - 32333) * 0.30
            else:
                rec.paye = 144483 + (taxable - 500000) * 0.35
            # Personal relief
            rec.paye = max(0, rec.paye - 2400)

    @api.depends('nhif', 'nssf', 'paye', 'other_deductions')
    def _compute_total_deductions(self):
        for rec in self:
            rec.total_deductions = (
                rec.nhif + rec.nssf +
                rec.paye + rec.other_deductions
            )

    @api.depends('gross_pay', 'total_deductions')
    def _compute_net_pay(self):
        for rec in self:
            rec.net_pay = rec.gross_pay - rec.total_deductions

    @api.depends('guard_id', 'date_from', 'date_to')
    def _compute_shifts_worked(self):
        for rec in self:
            if rec.guard_id and rec.date_from and rec.date_to:
                shifts = self.env['security.shift'].search_count([
                    ('guard_id', '=', rec.guard_id.id),
                    ('date', '>=', rec.date_from),
                    ('date', '<=', rec.date_to),
                    ('state', '=', 'done'),
                ])
                rec.shifts_worked = shifts
            else:
                rec.shifts_worked = 0

    # ── Auto-fill from Guard ──────────────────────────
    @api.onchange('guard_id')
    def _onchange_guard_id(self):
        if self.guard_id:
            self.basic_salary = self.guard_id.basic_salary
            self.house_allowance = self.guard_id.house_allowance
            self.transport_allowance = self.guard_id.transport_allowance

    # ── Action Buttons ────────────────────────────────
    def action_confirm(self):
        self.state = 'confirmed'

    def action_mark_paid(self):
        if not self.payment_method:
            raise ValidationError(
                "Please select a payment method."
            )
        if not self.payment_date:
            raise ValidationError(
                "Please enter a payment date."
            )
        self.write({
            'state': 'paid',
            'paid_by': self.env.user.id,
        })
        self.message_post(
            body=f"Salary paid via {self.payment_method}. "
                 f"Reference: {self.payment_reference or 'N/A'}. "
                 f"Amount: KES {self.net_pay:,.2f}",
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )

    def action_reset(self):
        self.state = 'draft'

    @api.constrains('guard_id', 'month', 'year')
    def _check_duplicate(self):
        for rec in self:
            duplicate = self.search([
                ('guard_id', '=', rec.guard_id.id),
                ('month', '=', rec.month),
                ('year', '=', rec.year),
                ('id', '!=', rec.id),
            ])
            if duplicate:
                raise ValidationError(
                    f"A payslip already exists for "
                    f"{rec.guard_id.name} for this month."
                )
