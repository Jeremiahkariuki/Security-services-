from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class SecurityGuard(models.Model):
    _name = 'security.guard'
    _description = 'Security Guard'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    # Personal Info
    name = fields.Char(string='Full Name', required=True, tracking=True)
    id_number = fields.Char(string='ID Number', required=True, tracking=True)
    phone = fields.Char(string='Phone Number')
    email = fields.Char(string='Email')
    photo = fields.Image(string='Photo', max_width=200, max_height=200)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string='Gender')
    date_of_birth = fields.Date(string='Date of Birth')

    # Employment Info
    employee_id = fields.Many2one('hr.employee', string='Linked Employee', tracking=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    ], string='Status', default='active', tracking=True)

    contract_start = fields.Date(string='Contract Start', required=True, tracking=True)
    contract_end = fields.Date(string='Contract End', required=True, tracking=True)
    contract_duration = fields.Integer(
        string='Contract Duration (months)',
        compute='_compute_contract_duration',
        store=True
    )

    # Assignment Info
    site_id = fields.Many2one('security.site', string='Assigned Site', tracking=True)
    supervisor_id = fields.Many2one(
        'security.guard',
        string='Supervisor',
        domain=[('status', '=', 'active')]
    )

    # Salary
    basic_salary = fields.Float(string='Basic Salary (KES)', tracking=True)
    house_allowance = fields.Float(string='House Allowance (KES)')
    transport_allowance = fields.Float(string='Transport Allowance (KES)')
    notes = fields.Text(string='Notes')

    @api.depends('contract_start', 'contract_end')
    def _compute_contract_duration(self):
        for rec in self:
            if rec.contract_start and rec.contract_end:
                delta = rec.contract_end - rec.contract_start
                rec.contract_duration = int(delta.days / 30)
            else:
                rec.contract_duration = 0

    @api.constrains('contract_start', 'contract_end')
    def _check_contract_dates(self):
        for rec in self:
            if rec.contract_start and rec.contract_end:
                if rec.contract_end < rec.contract_start:
                    raise ValidationError(
                        "Contract end date cannot be before start date."
                    )

    def name_get(self):
        result = []
        for rec in self:
            name = f"[{rec.id_number}] {rec.name}" if rec.id_number else rec.name
            result.append((rec.id, name))
        return result

    def action_open_fire_wizard(self):
        return {
            'name': 'Terminate / Suspend Guard',
            'type': 'ir.actions.act_window',
            'res_model': 'fire.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_guard_id': self.id},
        }
