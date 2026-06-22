from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from datetime import date


class SecurityGuardPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        guard = request.env['security.guard'].sudo().search([
            ('email', '=', request.env.user.email)
        ], limit=1)
        if guard:
            if 'shift_count' in counters:
                values['shift_count'] = request.env[
                    'security.shift'].sudo().search_count([
                    ('guard_id', '=', guard.id)
                ])
            if 'payslip_count' in counters:
                values['payslip_count'] = request.env[
                    'security.payslip'].sudo().search_count([
                    ('guard_id', '=', guard.id),
                    ('state', '=', 'paid')
                ])
            if 'complaint_count' in counters:
                values['complaint_count'] = request.env[
                    'security.complaint'].sudo().search_count([
                    ('guard_id', '=', guard.id)
                ])
        return values

    @http.route(['/my/guard-dashboard'],
                type='http', auth='user', website=True)
    def guard_dashboard(self, **kwargs):
        guard = request.env['security.guard'].sudo().search([
            ('email', '=', request.env.user.email)
        ], limit=1)
        if not guard:
            return request.redirect('/my')

        today_shift = request.env['security.shift'].sudo().search([
            ('guard_id', '=', guard.id),
            ('date', '=', date.today()),
        ], limit=1)

        recent_shifts = request.env['security.shift'].sudo().search([
            ('guard_id', '=', guard.id),
        ], limit=5, order='date desc')

        payslips = request.env['security.payslip'].sudo().search([
            ('guard_id', '=', guard.id),
            ('state', '=', 'paid'),
        ], limit=6, order='date_from desc')

        complaints = request.env['security.complaint'].sudo().search([
            ('guard_id', '=', guard.id),
        ], limit=5, order='date_raised desc')

        recent_attendance = request.env[
            'security.attendance'].sudo().search([
            ('guard_id', '=', guard.id),
        ], limit=5, order='clock_in desc')

        values = {
            'guard': guard,
            'today_shift': today_shift,
            'recent_shifts': recent_shifts,
            'payslips': payslips,
            'complaints': complaints,
            'recent_attendance': recent_attendance,
            'page_name': 'guard_dashboard',
        }
        return request.render(
            'security_services.portal_guard_dashboard', values
        )

    @http.route(['/my/guard-payslips'],
                type='http', auth='user', website=True)
    def guard_payslips(self, **kwargs):
        guard = request.env['security.guard'].sudo().search([
            ('email', '=', request.env.user.email)
        ], limit=1)
        if not guard:
            return request.redirect('/my')

        payslips = request.env['security.payslip'].sudo().search([
            ('guard_id', '=', guard.id),
        ], order='date_from desc')

        values = {
            'guard': guard,
            'payslips': payslips,
            'page_name': 'guard_payslips',
        }
        return request.render(
            'security_services.portal_guard_payslips', values
        )

    @http.route(['/my/guard-complaints'],
                type='http', auth='user', website=True)
    def guard_complaints(self, **kwargs):
        guard = request.env['security.guard'].sudo().search([
            ('email', '=', request.env.user.email)
        ], limit=1)
        if not guard:
            return request.redirect('/my')

        complaints = request.env['security.complaint'].sudo().search([
            ('guard_id', '=', guard.id),
        ], order='date_raised desc')

        values = {
            'guard': guard,
            'complaints': complaints,
            'page_name': 'guard_complaints',
        }
        return request.render(
            'security_services.portal_guard_complaints', values
        )

    @http.route(['/my/guard-complaints/submit'],
                type='http', auth='user',
                website=True, methods=['POST'])
    def submit_complaint(self, **kwargs):
        guard = request.env['security.guard'].sudo().search([
            ('email', '=', request.env.user.email)
        ], limit=1)
        if guard:
            request.env['security.complaint'].sudo().create({
                'guard_id': guard.id,
                'subject': kwargs.get('subject'),
                'description': kwargs.get('description'),
                'complaint_type': kwargs.get('complaint_type'),
                'priority': kwargs.get('priority', 'medium'),
            })
        return request.redirect('/my/guard-complaints')
