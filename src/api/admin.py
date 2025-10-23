from django.contrib import admin
from .models import Customer, Loan

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'first_name', 'last_name', 'monthly_salary', 'approved_limit', 'current_debt')
    search_fields = ('first_name', 'last_name', 'customer_id')

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('loan_id', 'customer', 'loan_amount', 'interest_rate', 'tenure', 'end_date')
    search_fields = ('loan_id', 'customer__customer_id')