from odoo import models, fields, api


class HireWizard(models.TransientModel):
    _name = 'hire.wizard'
    _description = 'Hire Applicant Wizard'

    applicant_id = fields.Many2one('security.applicant', string='Applicant', required=True)
    contract_start = fields.Date(string='Contract Start', required=True, default=fields.Date.today)
    contract_end = fields.Date(string='Contract End', required=True)
    basic_salary = fields.Float(string='Basic Salary (KES)', required=True)
    house_allowance = fields.Float(string='House Allowance (KES)')
    transport_allowance = fields.Float(string='Transport Allowance (KES)')
    site_id = fields.Many2one('security.site', string='Assign to Site')

    def action_confirm_hire(self):
        applicant = self.applicant_id
        guard = self.env['security.guard'].create({
            'name': applicant.name,
            'phone': applicant.phone,
            'email': applicant.email,
            'id_number': applicant.id_number,
            'contract_start': self.contract_start,
            'contract_end': self.contract_end,
            'basic_salary': self.basic_salary,
            'house_allowance': self.house_allowance,
            'transport_allowance': self.transport_allowance,
            'site_id': self.site_id.id if self.site_id else False,
            'status': 'active',
        })
        applicant.write({
            'stage': 'hired',
            'guard_id': guard.id,
        })
        self.env['security.employment.action'].create({
            'guard_id': guard.id,
            'action_type': 'hire',
            'action_date': self.contract_start,
            'reason': 'Hired via recruitment process',
            'approved_by': self.env.user.id,
        })
        return {
            'name': 'Guard Profile',
            'type': 'ir.actions.act_window',
            'res_model': 'security.guard',
            'res_id': guard.id,
            'view_mode': 'form',
        }