from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Max
from .models import Customer, Loan
from . import services
from .serializers import (
    CustomerRegistrationSerializer, CustomerResponseSerializer,
    LoanEligibilityRequestSerializer, LoanEligibilityResponseSerializer,
    CreateLoanRequestSerializer, CreateLoanResponseSerializer,
    ViewLoanSerializer, ViewLoansByCustomerSerializer
)
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

class RegisterView(APIView):
    """
    API endpoint to register a new customer.
    POST /api/register/
    """
    def post(self, request):
        # 1. Validate incoming JSON data
        serializer = CustomerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            # 2. Call our business logic from services.py
            approved_limit = services.calculate_approved_limit(data['monthly_salary'])

            # --- START FIX ---
            # Manually find the next available customer_id
            max_id_obj = Customer.objects.aggregate(max_id=Max('customer_id'))
            new_customer_id = (max_id_obj['max_id'] or 0) + 1
            # --- END FIX ---

            # 3. Create the new customer in the database
            customer = Customer.objects.create(
                customer_id=new_customer_id,  # <-- We now provide the ID
                first_name=data['first_name'],
                last_name=data['last_name'],
                age=data.get('age'), # .get() safely handles if age is missing
                monthly_salary=data['monthly_salary'],
                phone_number=data['phone_number'],
                approved_limit=approved_limit
            )

            # 4. Serialize the created customer for the response
            response_serializer = CustomerResponseSerializer(customer)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        # If validation fails, return a 400 error with details
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckEligibilityView(APIView):
    """
    API endpoint to check loan eligibility for a customer.
    POST /api/check-eligibility/
    """
    def post(self, request):
        serializer = LoanEligibilityRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # All logic is in the service function
            eligibility_result = services.check_loan_eligibility(
                customer_id=data['customer_id'],
                loan_amount=data['loan_amount'],
                interest_rate=data['interest_rate'],
                tenure=data['tenure']
            )
            
            # Serialize the result dictionary
            response_serializer = LoanEligibilityResponseSerializer(eligibility_result)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateLoanView(APIView):
    """
    API endpoint to create a new loan, if eligible.
    POST /api/create-loan/
    """
    def post(self, request):
        serializer = CreateLoanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        data = serializer.validated_data
        customer_id = data['customer_id']
        loan_amount = data['loan_amount']
        interest_rate = data['interest_rate']
        tenure = data['tenure']
        
        # 1. Check eligibility first
        eligibility_result = services.check_loan_eligibility(
            customer_id=customer_id,
            loan_amount=loan_amount,
            interest_rate=interest_rate,
            tenure=tenure
        )
        
        loan_approved = eligibility_result['approval']
        monthly_installment = eligibility_result['monthly_installment']
        
        if not loan_approved:
            response_data = {
                'loan_id': None,
                'customer_id': customer_id,
                'loan_approved': False,
                'message': 'Loan not approved. Customer not eligible.',
                'monthly_installment': None
            }
            serializer = CreateLoanResponseSerializer(response_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # 2. If approved, create the loan
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
             return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

        start_date = date.today()
        # Calculate end_date based on tenure
        end_date = start_date + relativedelta(months=tenure)
        
        new_loan = Loan.objects.create(
            customer=customer,
            loan_amount=loan_amount,
            tenure=tenure,
            interest_rate=eligibility_result['corrected_interest_rate'], # Use corrected rate
            monthly_repayment=Decimal(str(monthly_installment)),
            emis_paid_on_time=0, # New loan
            start_date=start_date,
            end_date=end_date
        )
        
        # 3. Send success response
        response_data = {
            'loan_id': new_loan.loan_id,
            'customer_id': customer.customer_id,
            'loan_approved': True,
            'message': 'Loan approved and created successfully.',
            'monthly_installment': monthly_installment
        }
        serializer = CreateLoanResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ViewLoanView(APIView):
    """
    API endpoint to view details of a specific loan.
    GET /api/view-loan/<loan_id>/
    """
    def get(self, request, loan_id):
        try:
            # select_related('customer') is an optimization.
            # It fetches the related Customer data in the same database query.
            loan = Loan.objects.select_related('customer').get(loan_id=loan_id)
            serializer = ViewLoanSerializer(loan)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Loan.DoesNotExist:
            return Response({"error": "Loan not found"}, status=status.HTTP_404_NOT_FOUND)


class ViewLoansByCustomerView(APIView):
    """
    API endpoint to view all loans for a specific customer.
    GET /api/view-loans/<customer_id>/
    """
    def get(self, request, customer_id):
        # Check if customer exists first
        if not Customer.objects.filter(customer_id=customer_id).exists():
             return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
            
        loans = Loan.objects.filter(customer_id=customer_id)
        
        if not loans.exists():
            # Return an empty list, which is not an error
            return Response([], status=status.HTTP_200_OK) 
        
        serializer = ViewLoansByCustomerSerializer(loans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)