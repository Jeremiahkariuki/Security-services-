from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class TestSecurityGuard(TransactionCase):

    def setUp(self):
        super().setUp()
        # Create test client
        self.client = self.env['security.client'].create({
            'name': 'Test Security Client',
            'contact_person': 'John Doe',
            'phone': '0712345678',
            'email': 'john@test.com',
            'status': 'active',
        })
        # Create test site
        self.site = self.env['security.site'].create({
            'name': 'Test Site',
            'client_id': self.client.id,
            'location': 'Nairobi CBD',
            'risk_level': 'medium',
            'required_guards': 2,
            'status': 'active',
        })
        # Create test guard
        self.guard = self.env['security.guard'].create({
            'name': 'Test Guard',
            'id_number': 'TEST001',
            'phone': '0712345678',
            'email': 'guard@test.com',
            'contract_start': date.today(),
            'contract_end': date.today() + timedelta(days=365),
            'basic_salary': 25000,
            'house_allowance': 5000,
            'transport_allowance': 3000,
            'site_id': self.site.id,
            'status': 'active',
        })

    def test_guard_creation(self):
        """Test guard is created successfully"""
        self.assertEqual(self.guard.name, 'Test Guard')
        self.assertEqual(self.guard.status, 'active')
        self.assertEqual(self.guard.basic_salary, 25000)

    def test_contract_duration(self):
        """Test contract duration is computed correctly"""
        self.assertGreater(self.guard.contract_duration, 0)

    def test_contract_date_validation(self):
        """Test contract end cannot be before start"""
        with self.assertRaises(ValidationError):
            self.env['security.guard'].create({
                'name': 'Bad Guard',
                'id_number': 'BAD001',
                'contract_start': date.today(),
                'contract_end': date.today() - timedelta(days=1),
                'basic_salary': 20000,
            })

    def test_guard_status_change(self):
        """Test guard status can be changed"""
        self.guard.write({'status': 'suspended'})
        self.assertEqual(self.guard.status, 'suspended')

    def test_guard_site_assignment(self):
        """Test guard is assigned to site"""
        self.assertEqual(self.guard.site_id.id, self.site.id)
        self.assertIn(self.guard, self.site.guard_ids)

    def test_guard_name_get(self):
        """Test guard display name includes ID number"""
        display_name = self.guard.name_get()[0][1]
        self.assertIn('TEST001', display_name)
        self.assertIn('Test Guard', display_name)
