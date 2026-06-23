from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class TestSecurityShift(TransactionCase):

    def setUp(self):
        super().setUp()
        self.client = self.env['security.client'].create({
            'name': 'Shift Test Client',
            'status': 'active',
        })
        self.site = self.env['security.site'].create({
            'name': 'Shift Test Site',
            'client_id': self.client.id,
            'location': 'Westlands',
            'risk_level': 'high',
            'status': 'active',
        })
        self.guard = self.env['security.guard'].create({
            'name': 'Shift Test Guard',
            'id_number': 'SHIFT001',
            'contract_start': date.today(),
            'contract_end': date.today() + timedelta(days=365),
            'basic_salary': 30000,
            'site_id': self.site.id,
            'status': 'active',
        })
        self.shift = self.env['security.shift'].create({
            'guard_id': self.guard.id,
            'site_id': self.site.id,
            'date': date.today(),
            'shift_type': 'day',
        })

    def test_shift_creation(self):
        """Test shift is created successfully"""
        self.assertEqual(self.shift.state, 'draft')
        self.assertEqual(self.shift.shift_type, 'day')

    def test_shift_hours_computation(self):
        """Test hours worked is computed correctly"""
        self.assertEqual(self.shift.hours_worked, 12.0)

    def test_shift_name_computation(self):
        """Test shift name is computed"""
        self.assertIn('Shift Test Guard', self.shift.name)

    def test_shift_workflow(self):
        """Test shift state transitions"""
        self.shift.action_confirm()
        self.assertEqual(self.shift.state, 'confirmed')
        self.shift.action_start()
        self.assertEqual(self.shift.state, 'ongoing')
        self.shift.action_done()
        self.assertEqual(self.shift.state, 'done')

    def test_shift_cancellation(self):
        """Test shift can be cancelled"""
        self.shift.action_cancel()
        self.assertEqual(self.shift.state, 'cancelled')

    def test_double_booking_prevention(self):
        """Test guard cannot be double booked"""
        with self.assertRaises(ValidationError):
            self.env['security.shift'].create({
                'guard_id': self.guard.id,
                'site_id': self.site.id,
                'date': date.today(),
                'shift_type': 'day',
            })

    def test_night_shift_hours(self):
        """Test night shift is 12 hours"""
        night_shift = self.env['security.shift'].create({
            'guard_id': self.guard.id,
            'site_id': self.site.id,
            'date': date.today() + timedelta(days=1),
            'shift_type': 'night',
        })
        self.assertEqual(night_shift.hours_worked, 12.0)
