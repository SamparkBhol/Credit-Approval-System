from django.test import TestCase
from . import services
from decimal import Decimal

class ServiceFunctionTests(TestCase):
    
    def test_calculate_approved_limit(self):
        """
        Test that the approved limit is calculated correctly and rounded to the nearest lakh.
        """
        # Test case 1: Standard calculation, no rounding
        salary1 = Decimal('50000')
        expected_limit1 = Decimal('1800000')  # 36 * 50000 = 1,800,000
        self.assertEqual(services.calculate_approved_limit(salary1), expected_limit1)

        # Test case 2: Rounding down
        salary2 = Decimal('51000')
        expected_limit2 = Decimal('1800000')  # 36 * 51000 = 1,836,000 -> rounds down
        self.assertEqual(services.calculate_approved_limit(salary2), expected_limit2)

        # Test case 3: Rounding up (>= .5)
        salary3 = Decimal('55000')
        expected_limit3 = Decimal('2000000')  # 36 * 55000 = 1,980,000 -> rounds up
        self.assertEqual(services.calculate_approved_limit(salary3), expected_limit3)
        
    def test_calculate_monthly_installment(self):
        """
        Test the EMI calculation.
        """
        # Test with a known value
        principal = Decimal('100000')
        annual_rate = Decimal('10')
        tenure_months = 12
        # Using a standard EMI calculator, 100k @ 10% for 12mo = 8791.59
        expected_emi = 8791.59
        self.assertAlmostEqual(services.calculate_monthly_installment(principal, annual_rate, tenure_months), expected_emi, places=2)