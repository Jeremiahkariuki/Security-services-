from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class TestSecurityPayslip(TransactionCase):

    def setUp(self):
        super().setUp()
        self.guard = self.env['security.guard'].create({
            'name': 'Payslip Test Guard',
            'id_number': 'PAY001',
            'contract_start': date.today(),
            'contract_end': date.today() + timedelta(days=365),
            'basic_salary': 50000,
            'house_allowance': 10000,
            'transport_allowance': 5000,
            'status': 'active',
        })
        self.payslip = self.env['security.payslip'].create({
            'guard_id': self.guard.id,
            'month': '6',
            'year': 2026,
            'basic_salary': 50000,
            'house_allowance': 10000,
            'transport_allowance': 5000,
        })

    def test_payslip_creation(self):
        """Test payslip is created with sequence"""
        self.assertNotEqual(self.payslip.name, 'New')
        self.assertEqual(self.payslip.state, 'draft')

    def test_gross_pay_computation(self):
        """Test gross pay is computed correctly"""
        expected = 50000 + 10000 + 5000
        self.assertEqual(self.payslip.gross_pay, expected)

    def test_nhif_computation(self):
        """Test NHIF is computed based on gross"""
        self.assertGreater(self.payslip.nhif, 0)

    def test_nssf_computation(self):
        """Test NSSF is 6% of basic salary max 2160"""
        expected_nssf = min(50000 * 0.06, 2160)
        self.assertAlmostEqual(
            self.payslip.nssf, expected_nssf, places=2
        )

    def test_net_pay_less_than_gross(self):
        """Test net pay is less than gross pay"""
        self.assertLess(self.payslip.net_pay, self.payslip.gross_pay)

    def test_payslip_confirm(self):
        """Test payslip can be confirmed"""
        self.payslip.action_confirm()
        self.assertEqual(self.payslip.state, 'confirmed')

    def test_payslip_paid_without_method(self):
        """Test payslip cannot be paid without payment method"""
        self.payslip.action_confirm()
        with self.assertRaises(ValidationError):
            self.payslip.action_mark_paid()

    def test_payslip_paid_with_method(self):
        """Test payslip can be paid with payment method"""
        self.payslip.action_confirm()
        self.payslip.write({
            'payment_method': 'mpesa',
            'payment_date': date.today(),
            'payment_reference': 'MP001',
        })
        self.payslip.action_mark_paid()
        self.assertEqual(self.payslip.state, 'paid')

    def test_duplicate_payslip_prevention(self):
        """Test duplicate payslip for same month is prevented"""
        with self.assertRaises(ValidationError):
            self.env['security.payslip'].create({
                'guard_id': self.guard.id,
                'month': '6',
                'year': 2026,
                'basic_salary': 50000,
            })
