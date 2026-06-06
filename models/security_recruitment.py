from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SecurityVacancy(models.Model):
    _name = 'security.vacancy'
    _description = 'Security Job Vacancy'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'job_title'

    job_title = fields.Char(string='Job Title', required=True, tracking=True)
    site_id = fields.Many2one('security.site', string='Site', tracking=True)
    no_of_posts = fields.Integer(string='Number of Posts', default=1, tracking=True)
    posted_date = fields.Date(string='Posted Date', default=fields.Date.today, tracking=True)
    deadline = fields.Date(string='Application Deadline', tracking=True)
    description = fields.Text(string='Job Description')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'), ('closed', 'Closed')], string='Status', default='draft', tracking=True)
    applicant_ids = fields.One2many('security.applicant', 'vacancy_id', string='Applicants')
    applicant_count = fields.Integer(string='Applicants', compute='_compute_applicant_count')

    def _compute_applicant_count(self):
        for rec in self:
            rec.applicant_count = len(rec.applicant_ids)

    def action_open(self):
        self.state = 'open'

    def action_close(self):
        self.state = 'closed'

    def action_view_applicants(self):
        return {'name': 'Applicants', 'type': 'ir.actions.act_window', 'res_model': 'security.applicant', 'view_mode': 'kanban,tree,form', 'domain': [('vacancy_id', '=', self.id)], 'context': {'default_vacancy_id': self.id}}


class SecurityApplicant(models.Model):
    _name = 'security.applicant'
    _description = 'Security Guard Applicant'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Applicant Name', required=True, tracking=True)
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    id_number = fields.Char(string='ID Number')
    vacancy_id = fields.Many2one('security.vacancy', string='Applied For', tracking=True)
    interview_date = fields.Datetime(string='Interview Date', tracking=True)
    interviewer_id = fields.Many2one('res.users', string='Interviewer', tracking=True)
    stage = fields.Selection([('new', 'New Application'), ('screening', 'Screening'), ('interview', 'Interview'), ('offer', 'Offer'), ('hired', 'Hired'), ('rejected', 'Rejected')], string='Stage', default='new', tracking=True)
    notes = fields.Text(string='Interview Notes')
    date_applied = fields.Date(string='Date Applied', default=fields.Date.today)
    guard_id = fields.Many2one('security.guard', string='Created Guard', readonly=True)

    def action_screening(self):
        self.stage = 'screening'

    def action_interview(self):
        self.stage = 'interview'

    def action_offer(self):
        self.stage = 'offer'

    def action_reject(self):
        self.stage = 'rejected'

    def action_hire(self):
        return {'name': 'Hire Applicant', 'type': 'ir.actions.act_window', 'res_model': 'hire.wizard', 'view_mode': 'form', 'target': 'new', 'context': {'default_applicant_id': self.id}}


class SecurityEmploymentAction(models.Model):
    _name = 'security.employment.action'
    _description = 'Employment Action (Hire/Fire)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'guard_id'

    guard_id = fields.Many2one('security.guard', string='Guard', required=True, tracking=True)
    action_type = fields.Selection([('hire', 'Hire'), ('fire', 'Terminate'), ('suspend', 'Suspend'), ('reinstate', 'Reinstate')], string='Action', required=True, tracking=True)
    action_date = fields.Date(string='Action Date', default=fields.Date.today, required=True)
    reason = fields.Text(string='Reason', required=True, tracking=True)
    approved_by = fields.Many2one('res.users', string='Approved By', default=lambda self: self.env.user, tracking=True)
    documents = fields.Many2many('ir.attachment', string='Supporting Documents')
