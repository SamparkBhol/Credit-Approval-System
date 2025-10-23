from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum
from .models import Customer, Loan
from datetime import date
import math

def calculate_approved_limit(monthly_salary: Decimal) -> Decimal:
    """
    Calculates the approved limit based on monthly salary, rounded to the nearest lakh.
    """
    # 36 * 50000 = 1,800,000
    # 36 * 51000 = 1,836,000 -> rounds to 1,800,000
    # 36 * 55000 = 1,980,000 -> rounds to 2,000,000
    unrounded_limit = 36 * monthly_salary
    
    # Round to the nearest 100,000 (lakh)
    # We divide by 100,000, round it, then multiply back.
    rounded_limit = (unrounded_limit / 100000).to_integral_value(rounding=ROUND_HALF_UP) * 100000
    return rounded_limit

def get_customer_loans(customer_id: int):
    """
    Fetches a customer and their current outstanding debt.
    """
    try:
        customer = Customer.objects.get(pk=customer_id)
    except Customer.DoesNotExist:
        return None, None

    # Calculate current debt: Sum of 'monthly_repayment' for all loans
    # where the 'end_date' is in the future.
    today = date.today()
    current_debt_agg = customer.loans.filter(end_date__gt=today).aggregate(
        total_debt=Sum('monthly_repayment')
    )
    
    current_debt = current_debt_agg['total_debt'] or Decimal('0.00')
    customer.current_debt = current_debt
    customer.save()
    
    return customer, current_debt

def calculate_credit_score(customer: Customer) -> int:
    """
    Calculates a credit score based on a customer's loan history.
    """
    # 1. Past Loans paid on time
    # Ratio of total EMIs paid on time vs. total tenure of past loans
    past_loans = customer.loans.filter(end_date__lte=date.today())
    if past_loans.exists():
        total_emis_paid = past_loans.aggregate(total=Sum('emis_paid_on_time'))['total'] or 0
        total_tenure = past_loans.aggregate(total=Sum('tenure'))['total'] or 0
        if total_tenure > 0:
            payment_ratio = total_emis_paid / total_tenure
            score_a = int(payment_ratio * 30) # Max 30 points
        else:
            score_a = 0
    else:
        score_a = 30 # No past loans? Good start.
    
    # 2. Number of loans taken in the past
    num_past_loans = past_loans.count()
    if num_past_loans > 5:
        score_b = 20 # Experienced borrower
    elif 2 <= num_past_loans <= 5:
        score_b = 10
    else:
        score_b = 0 # Max 20 points
        
    # 3. Loan activity in current year
    current_year_loans = customer.loans.filter(start_date__year=date.today().year).count()
    if current_year_loans > 2:
        score_c = 0 # Too many recent loans is risky
    else:
        score_c = 15 # Max 15 points
        
    # 4. Loan approved limit vs. total loans
    # This checks if they are borrowing responsibly within their means
    all_loans_sum = customer.loans.aggregate(total=Sum('loan_amount'))['total'] or 0
    if all_loans_sum > customer.approved_limit:
        score_d = 0 # Borrowing more than approved limit!
    else:
        score_d = 35 # Max 35 points

    # --- Knock-out Rule ---
    # If sum of current active loans > approved limit, score is 0
    if customer.current_debt > customer.approved_limit:
        return 0

    total_score = score_a + score_b + score_c + score_d
    return min(total_score, 100) # Cap at 100

def calculate_monthly_installment(principal, annual_rate, tenure_months):
    """
    Calculates EMI using the formula:
    EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    """
    if tenure_months == 0:
        return principal
    r = float(annual_rate / 100 / 12)
    if r == 0:
        return principal / tenure_months
        
    P = float(principal)
    n = float(tenure_months)
    emi = P * r * (pow(1 + r, n)) / (pow(1 + r, n) - 1)
    return round(emi, 2)


def check_loan_eligibility(customer_id, loan_amount, interest_rate, tenure):
    """
    Checks if a customer is eligible for a new loan based on their credit score
    and current debt.
    """
    customer, current_debt = get_customer_loans(customer_id)
    if not customer:
        return {'approval': False, 'message': 'Customer not found'}

    credit_score = calculate_credit_score(customer)
    
    # Convert inputs to Decimal for calculations
    loan_amount = Decimal(str(loan_amount))
    interest_rate = Decimal(str(interest_rate))
    
    # Rule 1: Credit Score > 50
    if credit_score < 50:
        return {
            'customer_id': customer_id,
            'approval': False,
            'interest_rate': float(interest_rate),
            'corrected_interest_rate': None,
            'tenure': tenure,
            'monthly_installment': 0.0
        }
    
    # Rule 2: Check if new EMI is affordable
    new_monthly_installment = calculate_monthly_installment(loan_amount, interest_rate, tenure)
    total_monthly_debt = current_debt + Decimal(str(new_monthly_installment))
    
    if total_monthly_debt > (customer.monthly_salary * Decimal('0.5')):
        return {
            'customer_id': customer_id,
            'approval': False,
            'interest_rate': float(interest_rate),
            'corrected_interest_rate': None,
            'tenure': tenure,
            'monthly_installment': 0.0
        }

    # Rule 3: Adjust interest rate based on score
    corrected_interest_rate = interest_rate
    if credit_score > 50:
        # Eligible
        pass # Use provided interest rate
    elif 30 < credit_score <= 50:
        corrected_interest_rate = max(interest_rate, Decimal('12.0'))
    elif 10 < credit_score <= 30:
        corrected_interest_rate = max(interest_rate, Decimal('16.0'))
    else: # Score < 10
        return {
            'customer_id': customer_id,
            'approval': False,
            'interest_rate': float(interest_rate),
            'corrected_interest_rate': None,
            'tenure': tenure,
            'monthly_installment': 0.0
        }
    
    # Recalculate EMI if interest rate was corrected
    if corrected_interest_rate != interest_rate:
        new_monthly_installment = calculate_monthly_installment(loan_amount, corrected_interest_rate, tenure)
    
    return {
        'customer_id': customer_id,
        'approval': True,
        'interest_rate': float(interest_rate),
        'corrected_interest_rate': float(corrected_interest_rate),
        'tenure': tenure,
        'monthly_installment': float(new_monthly_installment)
    }