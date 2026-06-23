from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class TestSecurityComplaint(TransactionCase):

    def setUp(self):
        super().setUp()
        self.guard = self.env['security.guard'].create({
            'name': 'Complaint Test Guard',
            'id_number': 'CMP001',
            'contract_start': date.today(),
            'contract_end': date.today() + timedelta(days=365),
            'basic_salary': 25000,
            'status': 'active',
        })
        self.complaint = self.env['security.complaint'].create({
            'guard_id': self.guard.id,
            'subject': 'Test Complaint',
            'description': 'This is a test complaint description',
            'complaint_type': 'salary',
            'priority': 'medium',
        })

    def test_complaint_creation(self):
        """Test complaint is created with sequence"""
        self.assertNotEqual(self.complaint.name, 'New')
        self.assertEqual(self.complaint.state, 'new')

    def test_complaint_review(self):
        """Test complaint can be moved to review"""
        self.complaint.action_review()
        self.assertEqual(self.complaint.state, 'in_review')
        self.assertEqual(
            self.complaint.reviewed_by.id,
            self.env.user.id
        )

    def test_complaint_resolve_without_notes(self):
        """Test complaint cannot be resolved without notes"""
        self.complaint.action_review()
        with self.assertRaises(ValidationError):
            self.complaint.action_resolve()

    def test_complaint_resolve_with_notes(self):
        """Test complaint can be resolved with notes"""
        self.complaint.action_review()
        self.complaint.resolution_notes = 'Issue has been resolved'
        self.complaint.action_resolve()
        self.assertEqual(self.complaint.state, 'resolved')

    def test_complaint_close(self):
        """Test complaint can be closed after resolving"""
        self.complaint.action_review()
        self.complaint.resolution_notes = 'Resolved'
        self.complaint.action_resolve()
        self.complaint.action_close()
        self.assertEqual(self.complaint.state, 'closed')
