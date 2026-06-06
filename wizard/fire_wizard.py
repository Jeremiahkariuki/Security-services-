from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FireWizard(models.TransientModel):
    _name = 'fire.wizard'
    _description = 'Terminate Guard Wizard'

    guard_id = fields.Many2one('security.guard', string='Guard', required=True)
    action_type = fields.Selection([
        ('fire', 'Terminate'),
        ('suspend', 'Suspend'),
    ], string='Action', required=True, default='fire')
    reason = fields.Text(string='Reason', required=True)
    action_date = fields.Date(string='Effective Date', default=fields.Date.today, required=True)

    def action_confirm(self):
        if not self.reason:
            raise ValidationError("Please provide a reason.")
        new_status = 'terminated' if self.action_type == 'fire' else 'suspended'
        self.guard_id.write({'status': new_status})
        self.env['security.employment.action'].create({
            'guard_id': self.guard_id.id,
            'action_type': self.action_type,
            'action_date': self.action_date,
            'reason': self.reason,
            'approved_by': self.env.user.id,
        })
        return {'type': 'ir.actions.act_window_close'}