from rest_framework import serializers
from .models import Customer, Loan
from datetime import date
from dateutil.relativedelta import relativedelta

class CustomerRegistrationSerializer(serializers.ModelSerializer):
    monthly_income = serializers.DecimalField(max_digits=10, decimal_places=2, source='monthly_salary', write_only=True)
    class Meta:
        model = Customer
        fields = ('first_name', 'last_name', 'age', 'phone_number', 'monthly_income')
        extra_kwargs = {
            'age': {'required': False, 'allow_null': True}
        }


class CustomerResponseSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    monthly_income = serializers.DecimalField(source='monthly_salary', max_digits=10, decimal_places=2)

    class Meta:
        model = Customer
        fields = ('customer_id', 'name', 'age', 'monthly_income', 'approved_limit', 'phone_number')

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class LoanEligibilityRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()

class LoanEligibilityResponseSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    approval = serializers.BooleanField()
    interest_rate = serializers.FloatField()
    corrected_interest_rate = serializers.FloatField(allow_null=True)
    tenure = serializers.IntegerField()
    monthly_installment = serializers.FloatField()

class CreateLoanRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()


class CreateLoanResponseSerializer(serializers.Serializer):
    loan_id = serializers.IntegerField(allow_null=True)
    customer_id = serializers.IntegerField()
    loan_approved = serializers.BooleanField()
    message = serializers.CharField()
    monthly_installment = serializers.FloatField(allow_null=True)

class CustomerDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ('customer_id', 'first_name', 'last_name', 'phone_number', 'age')


class ViewLoanSerializer(serializers.ModelSerializer):
    customer = CustomerDetailSerializer()
    monthly_installment = serializers.DecimalField(source='monthly_repayment', max_digits=10, decimal_places=2)

    class Meta:
        model = Loan
        fields = ('loan_id', 'customer', 'loan_amount', 'interest_rate', 'monthly_installment', 'tenure')


class ViewLoansByCustomerSerializer(serializers.ModelSerializer):
    repayments_left = serializers.SerializerMethodField()
    monthly_installment = serializers.DecimalField(source='monthly_repayment', max_digits=10, decimal_places=2)

    class Meta:
        model = Loan
        fields = ('loan_id', 'loan_amount', 'interest_rate', 'monthly_installment', 'repayments_left')

    def get_repayments_left(self, obj):
        today = date.today()
        end_date = obj.end_date
        
        if today > end_date:
            return 0
    
        r = relativedelta(end_date, today)
        months_left = r.years * 12 + r.months
        if today.day < end_date.day and months_left == 0 and r.years == 0:
             months_left = 1
        elif today.day > end_date.day and months_left == 0 and r.years == 0:
            months_left = 0
        elif months_left > 0 and today.day < end_date.day:
            months_left += 1

        return max(0, months_left)